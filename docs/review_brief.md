# 导师评审讲稿 (Mentor Review Brief)

> 本文基于 2026-09-18 的真实跑通结果撰写。

---

## 1. 一句话定位 (One-liner)

**Quotation Bot** 是一个概念验证（PoC, Proof of Concept）：
从企业邮箱自动拉取邮件 → 用多智能体流水线（Multi-agent Pipeline）判断是否是**报价请求**（Quotation Request）→ 抽取关键信息 → 查询客户公司背景 + 内部产品目录 → 生成回复邮件**草稿**。

**当前不做**：不自动发信、没有人工审核（Human Review）界面、没有 Web UI。是纯命令行批处理脚本（CLI batch script），跑一次处理一批。

---

## 2. 架构图 (Architecture)

```text
Gmail 邮箱 (IMAP, 端口 993)
   │  uv run python -m email_retriever.retriever
   ▼
retrieved_email 表（元数据：发件人/主题）
queued_jobs 表（状态机起点 PENDING）
data/emails/<email_id>_email.json（邮件正文，落文件不落库）
   │
   │  uv run python -m agents_workflow.workflow
   ▼
┌─────────────────────────────────────────────────────────┐
│ 状态机 (State Machine)：5 步顺序执行，每步用一个 Agent    │
│                                                           │
│ PENDING                                                  │
│   │ Classifier Agent：是否是报价请求？                    │
│   ├─ 不是 → COMPLETED（终态）                             │
│   └─ 是   → CLASSIFIED                                   │
│              │ Extractor Agent：抽产品/数量/公司/联系人   │
│              ▼ EXTRACTED                                 │
│              │ External Research Agent：联网查公司背景    │
│              │ （工具：Tavily 搜索 API）                  │
│              ▼ RESEARCH_EXT                               │
│              │ Internal Research Agent：查内部产品目录     │
│              │ （工具：SQL 精确匹配 → Chroma 向量语义匹配）│
│              ▼ RESEARCH_INT                               │
│              │ Email Draft Agent：生成回复草稿             │
│              ▼ DRAFTED（当前终点，不发送）                 │
└─────────────────────────────────────────────────────────┘
```

每一步的结果都以 JSON 累加写入 `queued_jobs.meta_data` 字段，任何一步都能追溯上一步的输出。

### 设计亮点（可以在评审中主动讲）

| 亮点 | 说明 |
|---|---|
| 结构化输出 (Structured Output) | 每个 Agent 用 Pydantic `BaseModel` 强制约束 LLM 输出格式，不是自由文本 |
| 工具调用 (Tool Calling) | 数据库查询 / 联网搜索通过 Python 函数暴露给 Agent，LLM 不直接碰数据库或密钥 |
| 混合检索 (Hybrid Retrieval) | 产品查找：先 SQL 精确匹配 SKU/别名，找不到再用 Chroma 向量库做语义检索兜底 |
| 防幻觉 (Anti-hallucination) | 所有 prompt 明确写"缺信息就返回 None，不要编造"；草稿 Agent 禁止编造价格/库存/交期 |
| 邮件内容不可信 | 邮件正文只写文件，不进数据库、不当作系统指令，避免 Prompt Injection 风险 |
| Schema 版本管理 | 用 Alembic 做数据库迁移（Migration），代码不调用 `create_all()`，每次改表结构都有版本记录 |

---

## 3. 现在实测能跑通什么（今天真实运行结果）

我们今天做了一次端到端真实运行（连真实 Gmail 收件箱、真实 LLM），结果如下：

- **拉取邮件**：成功拉到 11 封新邮件，写入数据库 + JSON 文件。
- **流水线运行**：11 个任务全部处理完毕。
  - 10 封无关邮件（Google 安全通知、Tavily 欢迎邮件等）被 Classifier 正确判定为"非报价"，直接终止在 `COMPLETED`。
  - **1 封真实德文询价邮件**（询问包装线开箱机+封箱机报价）被正确识别为报价请求，一路走完全部 5 步，最终到达 `DRAFTED`：
    - Extractor 正确抽出：产品描述、性能参数、公司名"Schwäbische Nudelwerke GmbH"、联系人"Thomas Maier"、交期要求等。
    - Internal Research Agent 在我们的模拟纸箱产品目录里**诚实地**没找到这个工业设备产品，返回 `found: false`（**这正好验证了"防幻觉"设计**：目录里明明没有，Agent 没有瞎编）。
    - Draft Agent 据此生成了一封礼貌的"暂未找到该产品，请补充更多信息"的回信草稿，没有编造任何价格或型号。
- **产品目录数据**：3 个产品 / 8 个别名 / 3 条库存 / 6 条价格已加载进 SQLite，Chroma 向量库里也有对应 3 条向量，语义检索可用。

**结论：管道端到端跑通，行为符合设计预期（无关邮件被过滤，找不到的产品不编造）。**

### 今天顺手修的 3 个阻塞性 bug

1. `.env` 里 `LLM_MODEL` 缺少 OpenRouter 要求的供应商前缀（改成 `google/gemini-3.5-flash`），否则程序启动即报错。
2. `base_provider.py` 里 Ollama 分支写错了函数名（`os.get` 应为 `os.getenv`），选 Ollama 会直接崩溃。
3. `workflow.py` 里 Extractor 阶段会把 Classifier 的结果**覆盖掉**，现在改成合并；另外三个阶段原来"缺字段就 `continue`"会让任务**永久卡死**在某个状态，现在改成"跳过该步骤但仍推进状态"，并记录跳过原因（如 `external_research_skipped`），保证任务不会卡死。

---

## 4. 为什么 Codespaces 面板上有 4 个端口？

**这 4 个端口和本项目的代码无关。** 全仓库唯一出现的端口是 `.env` 里的 `IMAP_PORT=993`——这是连接 Gmail IMAP 服务器用的标准端口（IMAPS），而且是**出站连接**（程序去连 Gmail，不是本机开一个端口等别人连）。项目本身没有任何 Web 服务器、API 服务，不监听任何端口。

我们检查了当前容器实际在监听的端口，全部来自 **GitHub Codespaces / VS Code 远程开发环境自带的基础设施**：SSH（2222）、code-server 内部通信端口等。这些端口会随着你打开的扩展、终端数量浮动，不是我们代码产生的，评审时可以直接说明"本项目是纯批处理脚本，没有对外端口；面板上的端口来自开发环境本身"。

---

## 5. 已知限制 / 下一步 (Known Limitations & Next Steps)

这些是设计上**尚未做**，不是 bug，建议正面承认，对应 `plan.md` 里的规划：

| 限制 | 现状 | 计划 |
|---|---|---|
| 没有重试/失败状态 | 任一 LLM 调用异常会中断整个批次（我们实测中就遇到一次 Gemini 的瞬时性错误，重跑才继续） | 加 `FAILED` 状态 + 重试机制 |
| 没有人工审核 | `DRAFTED` 就是终点，不会真正发信 | 加审批/驳回/修订状态，人工确认后才发信 |
| External Research 依赖 Tavily Key | 今天没配 key，该步骤被跳过而非报错（这是我们今天加的降级处理） | 补齐 key 或做无 key 时的降级说明 |
| CI 配置过时 | `.github/workflows/ci.yml` 用 Python 3.9，项目实际要 3.11，且没有测试代码 | 需要重新配置 CI，补测试 |
| 邮件正文格式曾变更 | 旧版数据在 `data/emails_legacy/`，当前代码读取格式已统一为 `<email_id>_email.json` | 无需处理，仅存档 |

---

## 5b. 通俗版：今天做了哪些改动

把这个项目想成一条"邮件处理流水线"，之前有三个地方会卡住，今天修了四件事：

1. **配置对不上**：调用 LLM 的模型名少了供应商前缀（`google/`），程序一启动就报错，补上即可。
2. **代码打错字**：切换到 Ollama 本地模型的分支里把 `os.getenv` 写成了不存在的 `os.get`，选它必崩，已修正。
3. **流水线会丢数据、会卡死**：
   - 第 2 步（信息抽取）写结果时会把第 1 步（分类）的结果整个覆盖掉，改成"追加"。
   - 第 3/4/5 步原来"缺一个字段就直接跳过"，会让任务永远卡在中间状态。改成"这步做不了就记录原因，然后照常推进"，任务不会再卡死。
   - 联网查公司那一步依赖的 Tavily key 没配置时，原来会让整条流水线崩溃，现在改成优雅跳过。
4. **真机跑了一遍验证**：连真实 Gmail 拉了 11 封邮件，10 封无关邮件被正确过滤终止，1 封真实德文报价询价邮件跑完全部 5 步生成回复草稿；目录里找不到的产品，AI 诚实说"没找到"而不是编造——验证了防幻觉设计有效。

## 6. 导师可能会问的问题 (Anticipated Q&A)

**Q: 这个系统现在能自动回复客户邮件吗？**
A: 不能，目前只生成草稿，写入数据库，不发送。发送需要人工审核环节，这是有意设计的安全边界（Important Boundaries in README）。

**Q: 如果 LLM 判断错了怎么办（比如把报价邮件判断成无关邮件）？**
A: 目前没有人工复核环节，误判的邮件会直接终止在 COMPLETED，不会重新进入流程。这是下一步要补的（human review）。

**Q: 产品目录是真实数据还是假数据？**
A: 目前是 `mock_data/product_seed.json` 里的模拟纸箱产品（3 个 SKU），用于验证检索逻辑，非真实业务数据。

**Q: 为什么用 4 个不同的 LLM 供应商（Google/OpenAI/Ollama/Groq/OpenRouter）？**
A: 这是可插拔设计（Provider abstraction），方便后续按成本/延迟/隐私需求切换模型供应商，不是要同时用 4 个。当前实际用的是通过 OpenRouter 调用的 Gemini 3.5 Flash。

**Q: 数据安全怎么保证？**
A: 邮件正文只写本地文件，不进数据库、不当作系统指令直接执行（防 Prompt Injection）；`.env` 密钥不提交仓库；README 里也明确写了不要对生产邮箱跑测试。

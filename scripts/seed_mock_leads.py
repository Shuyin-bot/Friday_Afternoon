"""Seed the mock demo lead set into the pipeline as if it had been retrieved
from the real mailbox — without touching IMAP at all.

Source of truth: mock_data/leads/email_inbox.v1-demo.json, a *derived, not
frozen* subset of the frozen v1 mock dataset (see
the file's own `note` / `source_mapping`
fields). It lives in the sibling `mock_data/` directory in the local development 
environment, — NOT inside this repo — by design: it is fixture data for
demoing/evaluating the agent workflow, not part of the product itself.

Why a seed script instead of actually emailing these leads into the test
mailbox: the `from` addresses are synthetic (many use the reserved
`.example` TLD), so they cannot be delivered through real SMTP/IMAP with
correct SPF/DKIM, and doing so would also mix synthetic data into a mailbox
that already contains real test traffic. Instead this script reuses the
exact same `record_new_email` helper the real IMAP retriever uses, so a
seeded lead is byte-for-byte indistinguishable, to the rest of the
pipeline, from a real retrieved email: same `retrieved_email` row, same
`queued_jobs` PENDING row, same `data/emails/<id>_email.json` artifact
shape ({email_id, from, subject, content}).

Seeded email_ids live in a reserved range (90000 + the lead's numeric
suffix, e.g. LEAD-2026-016 -> 90016) that will never collide with a real
IMAP UID, so this script is safe to re-run and safe to reset independently
of real retrieved mail.

Usage:
    uv run python -m scripts.seed_mock_leads          # seed (idempotent)
    uv run python -m scripts.seed_mock_leads --reset  # delete seeded rows first, then reseed
"""
import argparse
import json
import os
from pathlib import Path
from turtle import reset

from db_contexts.sessions import SessionLocal
from db_contexts.models import QueuedJob, RetrievedEmail
from email_retriever.retriever import record_new_email

# 定义模拟邮件的ID范围，确保不会与真实邮件的UID冲突。
SEED_ID_BASE = 90000
SEED_ID_MAX = 90999

# Defaults to the sibling mock_data/ directory next to this repo. Override
# with MOCK_DATA_DIR if your layout differs.
# Path(__file__).resolve()得到当前文件的绝对路径，.parents[2]得到上两级目录，然后拼接mock_data/leads/email_inbox.v1-demo.json
DEFAULT_SOURCE = Path(__file__).resolve().parents[2] / "mock_data" / "leads" / "email_inbox.v1-demo.json"

if os.getenv("MOCK_DATA_DIR"):
    SOURCE_FILE = (
        Path(os.getenv("MOCK_DATA_DIR")) 
        / "leads"
        / "email_inbox.v1-demo.json"
    )
else:
    SOURCE_FILE = DEFAULT_SOURCE
# same as:
# SOURCE_FILE = Path(os.getenv("MOCK_DATA_DIR", "")) / "leads" / "email_inbox.v1-demo.json" \
#     if os.getenv("MOCK_DATA_DIR") else DEFAULT_SOURCE


def _seed_email_id(lead_id: str) -> int:
    """计算模拟邮件ID。Caculate seed email ID for a given lead ID. 
    LEAD-2026-016 -> 90016. Keeps the human-readable suffix for easy lookup."""
    # 从右边开始，按照 - 分割，最多分割一次；取列表最后一个元素，即 LEAD-2026-016 中的 016，
    # 转换为整数后加上 SEED_ID_BASE 得到 email_id。
    suffix = int(lead_id.rsplit("-", 1)[-1]) # 生成数据库使用的 ID
    email_id = SEED_ID_BASE + suffix
    if email_id > SEED_ID_MAX:
        raise ValueError(f"lead_id {lead_id} maps outside the reserved seed range")
    return email_id


def reset_seeded_rows() -> None:
    """删除以前导入的模拟邮件.
    目标：删除 90000 到 90999 范围内的邮件
    删除对应的任务
    删除对应的 JSON 文件 
    Delete previously seeded retrieved_email/queued_jobs rows and their
    JSON artifacts. Only ever touches the reserved 90000-90999 id range —
    never real IMAP-retrieved mail."""
    data_dir = os.getenv("DATA_DIR", os.getenv("DATA", "data"))
    with SessionLocal() as session: # 打开数据库会话/连接
        # 等价于SQL：
        # SELECT * FROM retrieved_email
        # WHERE email_id >= 90000
        #   AND email_id <= 90999;
        emails = (
            session.query(RetrievedEmail)
            .filter(RetrievedEmail.email_id >= SEED_ID_BASE, RetrievedEmail.email_id <= SEED_ID_MAX)
            .all()
        )
        count = len(emails)
        for e in emails:
            # 删除与该邮件相关的所有 queued_jobs
            # 注意区别e.email_id（外部邮件ID：90016）和 e.id（内部数据库主键ID）
            session.query(QueuedJob).filter_by(email_id=e.id).delete()
            # 找到JSON文件
            artifact = Path(data_dir) / "emails" / f"{e.email_id}_email.json"
            # 标记删除JSON文件，如果文件不存在则忽略
            artifact.unlink(missing_ok=True)
            # 标记删除数据库中的邮件记录
            session.delete(e)
        # 正式提交前面的删除操作
        session.commit()
    print(f"reset: removed {count} previously seeded lead(s)")


def seed_mock_leads(source_file: Path = SOURCE_FILE) -> None:
    """核心函数：导入模拟邮件（从指定的 JSON 文件）。负责：
    1. 找到模拟数据文件
    2. 读取 JSON
    3. 循环每一条 lead
    4. 生成安全的模拟邮件 ID
    5. 把邮件交给 record_new_email()
    6. 统计新增了多少条、跳过了多少条"""
    if not source_file.exists():
        raise FileNotFoundError(
            f"{source_file} not found. Set MOCK_DATA_DIR to the directory that "
            "contains leads/email_inbox.v1-demo.json if mock_data/ is not a "
            "sibling of this repo."
        )

    data = json.loads(source_file.read_text(encoding="utf-8"))
    leads = data["leads"]

    created = 0
    skipped = 0
    for lead in leads:
        # 生成模拟邮件ID
        email_id = _seed_email_id(lead["lead_id"])
        raw = lead["raw_input"]
        # （最核心代码）调用 record_new_email() 来记录邮件，返回值表示是否是新邮件
        is_new = record_new_email(
            email_id=email_id,
            from_email=raw["from"],
            # 这里的 subject 字段加上了 [MOCK <lead_id>] 前缀，方便区分模拟邮件和真实邮件
            # 最终主题变成（示例）： [MOCK LEAD-2026-016] Need a case erector
            subject=f"[MOCK {lead['lead_id']}] {raw['subject']}",
            content=raw["body"],
        )
        if is_new:
            created += 1
        else:
            skipped += 1
    # 幂等性（Idempotence）：
    # 第一次运行： seeded 16 new lead(s), skipped 0 already-seeded lead(s)
    # 第二次运行： seeded 0 new lead(s), skipped 16 already-seeded lead(s)
    print(f"seeded {created} new lead(s), skipped {skipped} already-seeded lead(s) "
          f"(source: {source_file})")


if __name__ == "__main__":
    # 创建一个命令行参数解析器。

    # description=__doc__ 表示使用文件最上面的说明文字作为命令行帮助信息
    # 案例：运行 python -m scripts.seed_mock_leads --help 看到帮助说明
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        # 定义一个命令行选项 "--reset"
        # action="store_true" 表示：
        # 没写 --reset 时，值是 False; 写了 --reset 时，值是 True
        "--reset", action="store_true",
        help="delete previously seeded rows (id range 90000-90999) before reseeding",
    )
    args = parser.parse_args()

    if args.reset:
        reset_seeded_rows()
    # 无论有没有执行 reset，最后都会导入模拟数据。
    seed_mock_leads()

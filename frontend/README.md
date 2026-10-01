# Quotation Bot Frontend

React dashboard for monitoring quotation jobs and reviewing AI-generated
quotation drafts.

## 目录结构

```bash
├── index.html          # 唯一的 HTML 入口，里面有个空 <div id="root">
├── vite.config.js      # 构建工具配置
├── public/              # 静态资源(图标等)
└── src/
    ├── main.jsx         # JS 入口：把 React 挂到 #root 上
    ├── App.jsx          # 根组件：侧边栏 + 主内容区
    ├── theme.js         # MUI 主题(颜色/字体)
    ├── pages/           # 页面组件(DashboardPage, EmailQueuePage, HumanReviewPage, JobDetailPage)
    ├── components/      # 可复用小组件(Sidebar, StatusCards, ActivityList, HumanReviewCard)
    ├── services/        # 封装后端接口请求(jobService.js)
    ├── config/          # API 地址等配置
    └── data/            # 演示假数据
```

## Features

- View job statistics and workflow statuses
- Browse and inspect quotation jobs
- Dedicated **Email queue** page — filter chips + search across every
  inbound job in the pipeline
- Dedicated **Human review** page — every pending human-input request
  across all jobs, answerable inline, with a link back to the job detail
- Review original emails, research details, and quotation drafts
- Approve, edit, reject, or comment on drafts
- Receive live updates through Server-Sent Events

## Tech Stack

- React
- Vite
- Material UI
- Emotion
- JavaScript

## Setup

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend normally runs at:

```text
http://localhost:5173
```

The Vite development server proxies `/api` requests to the FastAPI backend at
`http://localhost:8000`.

Start the backend from the repo root:

```bash
uv run uvicorn api.main:app --reload --port 8000
```

## Other Commands

```bash
npm run build    # Create a production build
npm run preview  # Preview the production build
npm run lint     # Run Oxlint
```

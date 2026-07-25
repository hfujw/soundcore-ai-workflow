# 🎧 AI原生产品设计工作流

为 Soundcore Liberty 系列打造的智能洞察引擎。

## 项目简介

用户输入产品名 → 系统自动爬取多平台评价 → 4个AI Agent协作分析 → 生成产品洞察报告。

## 技术栈

- **后端**: FastAPI (Python)
- **前端**: React + shadcn/ui + Tailwind CSS
- **LLM**: DeepSeek v3
- **爬虫**: crawl4ai + Playwright + requests

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url>
cd soundcore-ai-workflow

# 2. 创建本地虚拟环境（环境隔离，不污染系统Python）
python -m venv env

# 3. 激活虚拟环境
# Windows:
env\Scripts\activate
# Mac/Linux:
source env/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 启动后端
cd backend
python main.py

# 6. 启动前端（另一个终端）
cd frontend
npm install
npm run dev
```

## 项目结构

```
soundcore-ai-workflow/
├── backend/          # FastAPI 后端（朱子钦负责）
├── frontend/         # React 前端（同学负责）
├── data/             # 所有数据（Git忽略，运行时自动创建）
├── env/              # 本地虚拟环境（Git忽略）
└── docs/             # 项目文档
```

## 分工

| 模块 | 负责人 | 内容 |
|------|--------|------|
| backend/engine/ | 朱子钦 | 爬虫、清洗、格式化、报告 |
| backend/utils/ | 朱子钦 | LLM调用、重试工具 |
| backend/config.py | 朱子钦 | 全局配置 |
| backend/agents/ | 同学 | 4个AI Agent |
| backend/prompts/ | 同学 | Agent的System Prompt |
| frontend/ | 同学 | React Web界面 |
| backend/routers/ | 联调 | API路由 |

## 环境说明

- 所有依赖安装在 `env/` 虚拟环境中，不依赖系统Python
- 所有数据存储在 `data/` 中
- 浏览器驱动（Chromium）由 Playwright 自动下载到项目内
- 两个开发者各自创建自己的 `env/`，互不影响
于金永
"""
================================================================
FastAPI 主入口 — 后端唯一启动文件
================================================================
职责: 启动 Web 服务器，挂载所有 API 路由
负责人: 朱子钦
依赖: routers/（路由模块）、config.py
被依赖: 前端通过 HTTP/WebSocket 连接这个服务

启动方式:
  cd backend
  python main.py

  # 或使用 uvicorn:
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload

API 文档:
  启动后访问 http://localhost:8000/docs （Swagger自动生成）
================================================================
"""
import sys
from pathlib import Path

# 确保项目根目录在 Python 搜索路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.pipeline import router as pipeline_router

# ── 创建 FastAPI 应用 ──
app = FastAPI(
    title="AI原生产品设计工作流",
    description="为 Soundcore Liberty 系列打造的智能洞察引擎",
    version="1.0.0",
)

# ── CORS 配置（允许前端跨域请求）─
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──
app.include_router(pipeline_router, prefix="/api")

# ── 根路径 ──
@app.get("/")
def root():
    """健康检查接口"""
    return {
        "service": "AI原生产品设计工作流",
        "status": "running",
        "docs": "/docs",
    }


# ── 启动入口 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 代码改动后自动重启
    )

"""
================================================================
流水线路由 — 分析流水线的 HTTP API
================================================================
职责: 提供 /api/start、/api/status、/api/report 等接口
负责人: 朱子钦（初版）、联调时和前端对接
依赖: engine/*（数据引擎）、agents/*（AI Agent）

API 列表:
  POST /api/start       → 启动一次分析（输入产品+平台）
  GET  /api/status      → 查询当前进度（给前端轮询）
  GET  /api/report/{id} → 下载报告文件
  WS   /ws/progress     → WebSocket 实时推送进度

TODO: 此文件目前为骨架，具体逻辑待实现
================================================================
"""
from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.post("/start")
def start_analysis(product: str, platforms: list[str]):
    """
    启动分析流水线

    TODO: 输入验证 → 爬取 → 清洗 → Agent分析 → 生成报告
    """
    # 骨架代码
    return {"message": "TODO", "product": product, "platforms": platforms}


@router.get("/status")
def get_status():
    """查询当前分析进度"""
    return {
        "state": "idle",  # idle | running | done
        "progress": 0.0,  # 0.0 ~ 1.0
        "agents": {
            "super_brain":       {"status": "waiting", "text": "等待中..."},
            "user_avatar":       {"status": "waiting", "text": "等待中..."},
            "competitor_scout":  {"status": "waiting", "text": "等待中..."},
            "industry_expert":   {"status": "waiting", "text": "等待中..."},
        },
    }


@router.get("/report/{report_id}")
def download_report(report_id: str):
    """下载生成的 Markdown 报告"""
    return {"message": "TODO", "report_id": report_id}


@router.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket 连接，实时推送分析进度给前端"""
    await websocket.accept()
    # TODO: 流水线运行时，每步更新推送给前端
    await websocket.send_json({"progress": 0.0, "message": "等待开始..."})
    await websocket.close()

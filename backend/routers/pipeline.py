"""
================================================================
流水线路由 — 完整分析流水线的 HTTP API
================================================================
职责: 提供 /api/start、/api/status、/api/report 等接口
负责人: 联调（由JY于2026-07-26完成实现）

API 列表:
  POST /api/start       → 启动一次分析（输入产品+平台+API Key）
  GET  /api/status      → 查询当前进度（给前端轮询）
  GET  /api/report/{id} → 下载报告文件
  WS   /ws/progress     → WebSocket 实时推送进度

执行流程:
  Phase 0: 爬虫并行抓取 → 清洗 → 格式统一
  Phase 1: 超级智囊(Agent1) → 竞品侦察兵(Agent3)
  Phase 2: 用户替身(Agent2) → 行业专家(Agent4)
  Phase 3: 报告生成
================================================================
"""
import asyncio
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, WebSocket, HTTPException
from pydantic import BaseModel

from config import DATA_REPORTS, PLATFORMS
from engine.scraper import scrape_reviews
from engine.cleaner import clean_reviews
from engine.normalizer import normalize, get_stats
from engine.reporter import generate_report
from agents.super_brain import SuperBrain
from agents.user_avatar import UserAvatar
from agents.competitor_scout import CompetitorScout
from agents.industry_expert import IndustryExpert

router = APIRouter()

# ── 共享状态（单次运行，MVP 够用）──
_state = {
    "state": "idle",          # idle | running | done | error
    "progress": 0.0,
    "message": "",
    "report_path": None,
    "agents": {
        "super_brain":       {"status": "waiting", "text": "等待中..."},
        "user_avatar":       {"status": "waiting", "text": "等待中..."},
        "competitor_scout":  {"status": "waiting", "text": "等待中..."},
        "industry_expert":   {"status": "waiting", "text": "等待中..."},
    },
    "stats": None,
    "product": "",
}

_active_ws: set[WebSocket] = set()


# ── 请求模型 ──
class StartRequest(BaseModel):
    product: str
    platforms: list[str] = ["reddit", "amazon", "bilibili", "jd"]
    api_key: str = ""


# ── 工具函数 ──
def _update(**kw):
    """更新状态并存入 _last_update 时间戳"""
    _state.update(**kw)
    _state["_last_update"] = datetime.now().isoformat()


async def _broadcast():
    """向所有 WebSocket 推送当前状态（已忽略断开的连接）"""
    dead = set()
    payload = json.dumps({
        "state": _state["state"],
        "progress": _state["progress"],
        "message": _state["message"],
        "agents": _state["agents"],
        "stats": _state["stats"],
    }, ensure_ascii=False)
    for ws in _active_ws:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _active_ws.difference_update(dead)


def _broadcast_sync():
    """同步上下文广播——创建新的事件循环"""
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_broadcast())
        loop.close()
    except Exception:
        pass  # 广播失败不影响主流程


# ═══════════════════════════════════════════════
# 后台流水线
# ═══════════════════════════════════════════════

def _run_pipeline(product: str, platforms: list[str], api_key: str):
    """完整分析流水线（在后台线程执行）"""
    # Windows GBK 修复：线程内的 stdout/stderr 设为 UTF-8
    if sys.platform == "win32":
        for stream_name in ("stdout", "stderr"):
            stream = getattr(sys, stream_name, None)
            if stream and hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except Exception:
                    pass

    try:
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key

        _update(state="running", progress=0.0,
                message="Starting pipeline...", product=product)

        # ── Phase 0: 爬取 + 清洗 ──
        _update(message="Scraping reviews from platforms...")
        _broadcast_sync()

        reviews_raw = asyncio.run(scrape_reviews(product, platforms))
        if not reviews_raw:
            _update(state="error", message="Crawler returned no data")
            _broadcast_sync()
            return

        all_raw = []
        for p, revs in reviews_raw.items():
            all_raw.extend(revs)

        _update(progress=0.12,
                message=f"Crawl complete: {len(all_raw)} raw reviews, cleaning...")
        _broadcast_sync()

        cleaned = clean_reviews(all_raw)
        normalized = normalize(reviews_raw, product)
        stats = get_stats(normalized)
        _state["stats"] = stats

        _update(progress=0.20,
                message=f"Clean complete: {len(normalized)} valid reviews")
        _broadcast_sync()

        # ── Phase 1a: 超级智囊 ──
        _update(message="[Agent1] SuperBrain analyzing user insights...")
        _state["agents"]["super_brain"]["status"] = "running"
        _state["agents"]["super_brain"]["text"] = "analyzing..."
        _broadcast_sync()

        sb = SuperBrain().analyze({
            "reviews": normalized,
            "product": product,
            "stats": stats,
        })

        _state["agents"]["super_brain"]["status"] = "done"
        _state["agents"]["super_brain"]["text"] = "done"
        _update(progress=0.40, message="[Agent1] SuperBrain done")
        _broadcast_sync()

        # ── Phase 1b: 竞品侦察兵 ──
        _update(message="[Agent3] CompetitorScout analyzing competition...")
        _state["agents"]["competitor_scout"]["status"] = "running"
        _state["agents"]["competitor_scout"]["text"] = "analyzing..."
        _broadcast_sync()

        cs = CompetitorScout().analyze({
            "super_brain_output": sb,
            "reviews": normalized,
            "product": product,
        })

        _state["agents"]["competitor_scout"]["status"] = "done"
        _state["agents"]["competitor_scout"]["text"] = "done"
        _update(progress=0.55, message="[Agent3] CompetitorScout done")
        _broadcast_sync()

        # ── Phase 2a: 用户替身 ──
        _update(message="[Agent2] UserAvatar stress-testing concepts...")
        _state["agents"]["user_avatar"]["status"] = "running"
        _state["agents"]["user_avatar"]["text"] = "analyzing..."
        _broadcast_sync()

        ua = UserAvatar().analyze({
            "super_brain_output": sb,
            "product": product,
        })

        _state["agents"]["user_avatar"]["status"] = "done"
        _state["agents"]["user_avatar"]["text"] = "done"
        _update(progress=0.70, message="[Agent2] UserAvatar done")
        _broadcast_sync()

        # ── Phase 2b: 行业专家 ──
        _update(message="[Agent4] IndustryExpert evaluating feasibility...")
        _state["agents"]["industry_expert"]["status"] = "running"
        _state["agents"]["industry_expert"]["text"] = "analyzing..."
        _broadcast_sync()

        ie = IndustryExpert().analyze({
            "super_brain_output": sb,
            "user_avatar_output": ua,
            "competitor_scout_output": cs,
            "product": product,
        })

        _state["agents"]["industry_expert"]["status"] = "done"
        _state["agents"]["industry_expert"]["text"] = "done"
        _update(progress=0.85, message="[Agent4] IndustryExpert done")
        _broadcast_sync()

        # ── Phase 3: 生成报告 ──
        _update(message="Generating report...")
        _broadcast_sync()

        report_path = generate_report(product, stats, {
            "super_brain": sb,
            "user_avatar": ua,
            "competitor_scout": cs,
            "industry_expert": ie,
        })

        _state["report_path"] = report_path
        _update(state="done", progress=1.0, message="Report generated!")
        _broadcast_sync()

    except Exception as e:
        import traceback
        traceback.print_exc()
        err_msg = str(e)
        # 如果异常信息包含不可编码字符，提取代用文本
        _update(state="error", message=f"Error: {err_msg}")
        _broadcast_sync()


# ═══════════════════════════════════════════════
# HTTP 路由
# ═══════════════════════════════════════════════

@router.post("/start")
async def start_analysis(req: StartRequest):
    """启动一次产品分析流水线"""
    if _state["state"] == "running":
        raise HTTPException(400, detail="已有分析任务正在运行，请等待完成")

    # 重置状态
    _update(
        state="running", progress=0.0, message="启动中...",
        report_path=None, product=req.product, stats=None,
        agents={
            "super_brain":       {"status": "waiting", "text": "等待中..."},
            "user_avatar":       {"status": "waiting", "text": "等待中..."},
            "competitor_scout":  {"status": "waiting", "text": "等待中..."},
            "industry_expert":   {"status": "waiting", "text": "等待中..."},
        },
    )

    # 后台线程运行（Agent LLM 调用是同步的，不能阻塞 FastAPI 事件循环）
    t = threading.Thread(
        target=_run_pipeline,
        args=(req.product, req.platforms, req.api_key),
        daemon=True,
    )
    t.start()

    return {"message": "流水线已启动", "product": req.product}


@router.get("/status")
def get_status():
    """获取当前分析进度"""
    return {
        "state": _state["state"],
        "progress": _state["progress"],
        "message": _state["message"],
        "agents": _state["agents"],
        "stats": _state["stats"],
        "product": _state["product"],
        "report_path": _state.get("report_path"),
    }


@router.get("/report/{report_name}")
def download_report(report_name: str):
    """下载生成的 Markdown 报告内容"""
    safe_name = Path(report_name).name  # 防路径穿越
    report_file = DATA_REPORTS / safe_name
    if not report_file.exists():
        raise HTTPException(404, "报告不存在")
    content = report_file.read_text(encoding="utf-8")
    return {"content": content, "filename": safe_name}


@router.get("/preset-products")
def get_preset_products():
    """获取预设产品列表"""
    from config import PRESET_PRODUCTS, COMPETITORS
    return {"products": PRESET_PRODUCTS, "competitors": COMPETITORS,
            "platforms": {k: v for k, v in PLATFORMS.items() if v["enabled"]}}


# ═══════════════════════════════════════════════
# WebSocket 实时推送
# ═══════════════════════════════════════════════

@router.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket 连接，实时推送分析进度"""
    await websocket.accept()
    _active_ws.add(websocket)
    try:
        # 先发一次当前状态
        await _broadcast()
        # 保持连接，等待关闭
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except Exception:
                break
    finally:
        _active_ws.discard(websocket)

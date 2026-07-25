"""
================================================================
跨平台格式统一模块
================================================================
职责: 把各平台不同格式的评价 → 变成统一格式
负责人: 朱子钦
依赖: 无（纯数据处理）
被依赖: routers/pipeline.py

统一格式（每一行是一条评价）:
  {
    "platform": str,     # "jd" | "amazon" | "reddit" | "bilibili"
    "product":  str,     # 产品名（用户输入的那个）
    "user":     str,     # 用户名（匿名则 "anonymous"）
    "rating":   float|null,  # 评分 1.0-5.0，无法识别时为 null
    "content":  str,     # 评价文本（已清洗）
    "time":     str,     # ISO 8601 格式时间
    "language": str,     # "zh" | "en"（基于中文字符占比自动检测）
  }

归一化规则:
  - 评分: "4.0 out of 5" → 4.0, "★★★☆☆" → 3.0, 十分制→÷2
  - 时间: "2周前" → 推算日期, "July 15, 2026" → ISO 8601
  - 语言: 中文字符占比 > 15% → "zh", 否则 → "en"

核心函数:
  normalize(raw_data, product_name) → list[统一格式dict]
  get_stats(unified_reviews) → dict（总数、平台分布、平均分、语言分布）

TODO: 此文件目前为骨架，具体归一化逻辑待完善
================================================================
"""
import pandas as pd
from datetime import datetime


def normalize(raw_data: dict[str, list[dict]], product_name: str) -> list[dict]:
    """
    跨平台格式统一

    Args:
        raw_data:      {"reddit": [review, ...], "jd": [review, ...], ...}
        product_name:  产品名

    Returns:
        统一格式的评价列表
    """
    unified = []
    for platform, reviews in raw_data.items():
        if not reviews:
            continue
        for r in reviews:
            unified.append({
                "platform": platform,
                "product": product_name,
                "user": r.get("user", "anonymous"),
                "rating": _norm_rating(r.get("rating")),
                "content": r.get("content", ""),
                "time": _norm_time(r.get("time")),
                "language": _detect_language(r.get("content", "")),
            })
    return unified


def get_stats(reviews: list[dict]) -> dict:
    """生成基本统计，给 Agent1 和报告使用"""
    if not reviews:
        return {"total": 0, "platforms": {}, "avg_rating": None, "language": {"zh": 0, "en": 0}}

    df = pd.DataFrame(reviews)
    platform_counts = df["platform"].value_counts().to_dict()
    ratings = [r["rating"] for r in reviews if r["rating"] is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    return {
        "total": len(reviews),
        "platforms": platform_counts,
        "avg_rating": avg_rating,
        "language": {
            "zh": len([r for r in reviews if r["language"] == "zh"]),
            "en": len([r for r in reviews if r["language"] == "en"]),
        },
    }


def _norm_rating(rating) -> float | None:
    """评分归一化 → 1.0 ~ 5.0"""
    if rating is None:
        return None
    try:
        r = float(rating)
        if 5 < r <= 10:
            r = r / 2        # 十分制 → 五分制
        elif r > 10:
            r = r / 20       # 百分比 → 五分制
        return round(max(1.0, min(5.0, r)), 1)
    except (ValueError, TypeError):
        return None


def _norm_time(t) -> str:
    """时间归一化 → ISO 8601"""
    if not t:
        return datetime.now().isoformat()
    if isinstance(t, (int, float)):
        return datetime.fromtimestamp(t).isoformat()
    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y"]:
        try:
            return datetime.strptime(str(t)[:19], fmt).isoformat()
        except (ValueError, IndexError):
            continue
    return str(t)


def _detect_language(text: str) -> str:
    """语言检测：中文字符占比 > 15% → zh，否则 → en"""
    if not text:
        return "unknown"
    chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
    total = len(text.replace(' ', ''))
    return "zh" if (total > 0 and chinese_chars / total > 0.15) else "en"

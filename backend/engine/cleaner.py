"""
================================================================
数据清洗模块
================================================================
职责: 输入原始评价列表 → 输出清洗后评价列表
负责人: 朱子钦
依赖: 无（纯数据处理）
被依赖: routers/pipeline.py

清洗流程（4步管线）:
  Step 1: 去空 — 删除 content 为空或纯符号的评价
  Step 2: 去HTML — 删除 <br> <div> &nbsp; 等HTML标签和实体
  Step 3: 去重 — 同平台+同用户+内容前50字相同 → 只留一条
  Step 4: 去短 — 删除清洗后 < 5个有效字符的评价

核心函数:
  clean_reviews(reviews: list[dict]) → list[dict]

TODO: 此文件目前为骨架，具体清洗逻辑待实现
  (清洗标准和产物需要专门设计——朱子钦后续安排)
================================================================
"""
import re
import hashlib


def clean_reviews(reviews: list[dict]) -> list[dict]:
    """
    清洗主入口

    Args:
        reviews: 爬虫原始评价列表

    Returns:
        清洗后的评价列表（数量 ≤ 输入数量）
    """
    if not reviews:
        return []

    cleaned = reviews

    # Step 1: 去空
    cleaned = [r for r in cleaned if _is_meaningful(r.get("content", ""))]

    # Step 2: 去HTML
    for r in cleaned:
        r["content"] = _clean_text(r["content"])

    # Step 3: 去重
    cleaned = _deduplicate(cleaned)

    # Step 4: 去短
    cleaned = [r for r in cleaned if len(r.get("content", "")) >= 5]

    return cleaned


def _is_meaningful(text: str) -> bool:
    """检查文本是否有实际内容（不是空或纯符号）"""
    if not text or not text.strip():
        return False
    stripped = re.sub(r'[^\w一-鿿]', '', text.strip())
    return len(stripped) > 0


def _clean_text(text: str) -> str:
    """清洗单条文本：去HTML标签、去URL、去多余空格、去HTML实体"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    entities = {'&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
                '&quot;': '"', '&#39;': "'"}
    for entity, replacement in entities.items():
        text = text.replace(entity, replacement)
    return text.strip()


def _deduplicate(reviews: list[dict]) -> list[dict]:
    """去重：相同平台+相同用户+内容前50字相同 → 只留第一条"""
    seen = set()
    unique = []
    for r in reviews:
        content_preview = r.get("content", "")[:50]
        fingerprint = f"{r.get('platform', '')}:{r.get('user', '')}:{content_preview}"
        fp_hash = hashlib.md5(fingerprint.encode()).hexdigest()
        if fp_hash not in seen:
            seen.add(fp_hash)
            unique.append(r)
    return unique

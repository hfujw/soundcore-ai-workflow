"""
================================================================
爬虫调度器 — 混合策略
================================================================
职责: 给产品名+平台列表 → 返回各平台评价数据
负责人: 朱子钦
依赖: crawl4ai, Playwright, requests, config.py
被依赖: routers/pipeline.py

爬取策略（按平台）:
  Reddit  → crawl4ai 主力 → 失败则 requests + .json API 兜底
  Amazon  → crawl4ai 主力 → 失败则 requests + BS4 兜底
  B站     → crawl4ai 主力 → 失败则 requests 评论API 兜底
  京东    → 始终 Playwright（crawl4ai 大概率被风控拦截）
  小红书  → MVP阶段返回空列表（开闭原则预留接口）

核心函数:
  scrape_reviews(product_name, platforms) → dict[platform, list[review]]
    review 格式: {platform, user, rating, content, time}

TODO: 此文件目前为骨架，具体爬虫逻辑待实现
================================================================
"""
import asyncio
import json
import time
from datetime import datetime
from config import DATA_RAW, MAX_REVIEWS_PER_PLATFORM, CRAWL_DELAY_SECONDS, PLATFORMS, JD_STATE_FILE


async def scrape_reviews(product_name: str, platforms: list[str]) -> dict:
    """
    爬虫主入口 — 对指定平台爬取评价

    Args:
        product_name: 产品名，如 "Soundcore Liberty 5 Pro Max"
        platforms:   平台列表，如 ["reddit", "amazon", "jd", "bilibili"]

    Returns:
        {platform: [review_dict, ...], ...}
        每个 review_dict: {platform, user, rating, content, time}

    异常处理:
        单个平台失败 → 返回空列表，不影响其他平台
        全平台失败 → 返回空 dict，由调用方处理
    """
    results = {}
    for platform in platforms:
        if platform not in PLATFORMS or not PLATFORMS[platform]["enabled"]:
            continue
        print(f"  🕷️ 爬取 {PLATFORMS[platform]['name']}...")
        try:
            # TODO: 根据平台选择爬虫
            # scraper = _get_scraper(platform)
            # reviews = await scraper(product_name)
            reviews = []  # 骨架
            results[platform] = reviews
            _save_raw(platform, product_name, reviews)
        except Exception as e:
            print(f"  ❌ {platform} 爬取失败: {e}")
            results[platform] = []
        time.sleep(CRAWL_DELAY_SECONDS)
    return results


def _save_raw(platform: str, product: str, reviews: list[dict]):
    """保存原始爬虫数据到 data/raw/"""
    if not reviews:
        return
    safe_name = product.replace(" ", "_").replace("/", "_")
    date_str = datetime.now().strftime("%Y%m%d")
    fname = DATA_RAW / f"{platform}_{safe_name}_{date_str}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"    💾 保存 {len(reviews)} 条 → {fname.name}")


# ── 以下函数为骨架，具体实现待填充 ──

async def _scrape_reddit(product_name: str) -> list[dict]:
    """Reddit: crawl4ai主力 → requests .json API 兜底"""
    # TODO: 实现
    return []


async def _scrape_amazon(product_name: str) -> list[dict]:
    """Amazon: crawl4ai主力 → requests BS4 兜底"""
    # TODO: 实现
    return []


async def _scrape_bilibili(product_name: str) -> list[dict]:
    """B站: crawl4ai主力 → requests 评论API 兜底"""
    # TODO: 实现
    return []


async def _scrape_jd(product_name: str) -> list[dict]:
    """京东: Playwright 浏览器自动化"""
    # TODO: 实现（复用之前写的 jd_final.py 思路）
    return []


async def _scrape_xiaohongshu(product_name: str) -> list[dict]:
    """
    小红书 — MVP阶段跳过
    遵循开闭原则：对扩展开放，对修改关闭
    后续实现只需修改此函数，不影响任何其他模块
    """
    return []

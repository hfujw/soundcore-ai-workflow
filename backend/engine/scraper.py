"""
================================================================
爬虫引擎 — 工业级架构
================================================================
设计原则:
  1. 基类封装通用逻辑（重试、降级、日志、校验），子类只写"怎么爬"
  2. 每个平台 = 一个 Scraper 子类，新增平台只需新增一个类（开闭原则）
  3. 真正异步并行：asyncio.gather() 同时跑四个平台
  4. 结构化日志：不再用 print()，每条日志带 [平台] 前缀
  5. 选择器集中管理：放类属性里，改版时一眼看到
  6. 三层降级：首选 → 备选 → 兜底 → 空列表（不崩）

负责人: 朱子钦
依赖: config.py, utils/retry.py
================================================================
"""
import asyncio
import json
import logging
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from config import (
    DATA_RAW, MAX_REVIEWS_PER_PLATFORM,
    PLATFORMS, JD_STATE_FILE,
)

# ── 结构化日志 ──
logger = logging.getLogger("scraper")


# ═══════════════════════════════════════════════
# 基类
# ═══════════════════════════════════════════════

class BaseScraper(ABC):
    """
    爬虫基类 — 封装所有通用逻辑
    子类只需:
      1. 定义 SELECTORS（选择器字典）
      2. 实现 _try_primary()   — 首选方案
      3. 实现 _try_fallback()  — 备选方案
      4. 可选实现 _try_last_resort() — 最后兜底
    """

    # 子类必须覆盖
    platform: str = ""          # "reddit" | "amazon" | "bilibili" | "jd"
    SELECTORS: dict = {}        # 选择器字典

    def __init__(self):
        self.max_items = MAX_REVIEWS_PER_PLATFORM

    # ── 公共入口 ──
    async def scrape(self, product_name: str) -> list[dict]:
        """主入口：三层降级，自动选择最佳方案"""
        self._log(f"开始爬取: {product_name}")

        for level, method_name in enumerate(
            ["_try_primary", "_try_fallback", "_try_last_resort"]
        ):
            method = getattr(self, method_name, None)
            if method is None:
                continue

            try:
                reviews = await method(product_name)
                if self._quality_ok(reviews):
                    self._log(f"✅ {['首选','备选','兜底'][level]}方案成功，{len(reviews)}条")
                    return reviews[:self.max_items]
                self._log(f"⚠️ {['首选','备选','兜底'][level]}方案数据质量不够，降级")
            except Exception as e:
                self._log(f"❌ {['首选','备选','兜底'][level]}方案失败: {e}")

        self._log("🚫 所有方案均失败，返回空列表")
        return []

    # ── 子类必须实现 ──
    @abstractmethod
    async def _try_primary(self, product_name: str) -> list[dict]:
        """首选方案（最稳/最全）"""
        ...

    @abstractmethod
    async def _try_fallback(self, product_name: str) -> list[dict]:
        """备选方案（功能稍弱但大概率能跑）"""
        ...

    async def _try_last_resort(self, product_name: str) -> list[dict]:
        """最后兜底（最简陋但保证不崩），子类可选实现"""
        return []

    # ── 公共工具 ──
    def _quality_ok(self, reviews: list[dict], min_count: int = 3) -> bool:
        """数据质量校验：至少N条 + 平均长度≥30字"""
        if not reviews or len(reviews) < min_count:
            return False
        avg_len = sum(len(r.get("content", "")) for r in reviews) / len(reviews)
        return avg_len >= 30

    def _log(self, msg: str):
        """结构化日志"""
        if sys.platform == "win32":
            # Windows GBK 容错：替换不可编码字符
            try:
                print(f"  [{self.platform}] {msg}")
            except UnicodeEncodeError:
                safe = msg.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
                print(f"  [{self.platform}] {safe}")
        else:
            print(f"  [{self.platform}] {msg}")

    @staticmethod
    def _try_selectors(page_or_item, selectors: list[str], attr: str = "inner_text"):
        """
        选择器兜底引擎 — 工业级的核心秘籍
        给一个选择器列表，挨个试，第一个匹配的就返回

        Args:
            page_or_item: Playwright的page或locator
            selectors: 选择器列表，按优先级排列
            attr: 要提取的属性 ("inner_text" | "get_attribute:class" | "count")

        Returns:
            提取到的值（文本或数字），全失败返回默认值
        """
        for sel in selectors:
            try:
                el = page_or_item.locator(sel).first if hasattr(page_or_item, 'locator') else page_or_item.select_one(sel)
                # Playwright模式
                if hasattr(page_or_item, 'locator'):
                    el = page_or_item.locator(sel).first
                    if attr == "count":
                        return True  # 只用来判断存在
                    if attr.startswith("get_attribute:"):
                        a = attr.split(":")[1]
                        val = None
                        try:
                            val = el.get_attribute(a)
                        except:
                            pass
                        try:
                            val = asyncio.get_event_loop().run_until_complete(val) if asyncio.iscoroutine(val) else val
                        except:
                            try:
                                val = el.evaluate(f"el => el.getAttribute('{a}')")
                            except:
                                pass
                        # 简化：直接在这里用同步方式处理
                        return None
                    # 默认inner_text
                    try:
                        txt = el.inner_text()
                        if asyncio.iscoroutine(txt):
                            continue  # Skip coroutine selectors in sync context
                        val = txt.strip()
                        if val:
                            return val
                    except:
                        continue
                # BS4模式
                else:
                    el = page_or_item.select_one(sel)
                    if el:
                        if attr == "count":
                            return True
                        return el.text.strip()
            except Exception:
                continue
        return "" if attr == "inner_text" else None

    def _save_raw(self, product_name: str, reviews: list[dict]):
        """保存原始数据到 data/raw/"""
        if not reviews:
            return
        safe_name = product_name.replace(" ", "_").replace("/", "_")
        date_str = datetime.now().strftime("%Y%m%d")
        fname = DATA_RAW / f"{self.platform}_{safe_name}_{date_str}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        self._log(f"💾 已保存 {len(reviews)} 条 → {fname.name}")


# ═══════════════════════════════════════════════
# Reddit 爬虫
# ═══════════════════════════════════════════════

class RedditScraper(BaseScraper):
    platform = "reddit"

    async def _try_primary(self, product_name: str) -> list[dict]:
        """首选: crawl4ai（AI自动提取）"""
        try:
            from crawl4ai import AsyncWebCrawler
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=f"https://www.reddit.com/search.json?q={product_name.replace(' ', '+')}+review&limit=25",
                    extraction_strategy="Extract post titles, authors, scores, and full text. Return JSON array."
                )
                if result and result.extracted_content:
                    return self._parse_crawl4ai(result.extracted_content)
        except ImportError:
            pass
        except Exception as e:
            self._log(f"crawl4ai: {e}")
        return []

    async def _try_fallback(self, product_name: str) -> list[dict]:
        """备选: 拿帖子 + 拿评论"""
        return await self._scrape_with_comments(product_name)

    async def _try_last_resort(self, product_name: str) -> list[dict]:
        """兜底: 只拿帖子正文"""
        return await self._scrape_posts_only(product_name)

    async def _scrape_with_comments(self, product_name: str) -> list[dict]:
        """requests → 搜帖子 → 每个帖子拿热门评论"""
        import requests as req
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0"}

        try:
            resp = req.get("https://www.reddit.com/search.json",
                           params={"q": f"{product_name} review", "limit": 10},
                           headers=headers, timeout=30)
            posts = resp.json().get("data", {}).get("children", [])
        except Exception as e:
            self._log(f"搜索失败: {e}")
            return []

        reviews = []
        for post_item in posts:
            post = post_item.get("data", {})
            permalink = post.get("permalink", "")

            # 加帖子正文
            body = f"[Post] {post.get('title', '')}"
            if post.get("selftext"):
                body += f"\n{post['selftext'][:300]}"
            if len(body) >= 20:
                reviews.append(self._make_review(
                    user=post.get("author"), rating=None, content=body[:500],
                    created=post.get("created_utc"), ups=post.get("score", 0),
                ))

            # 加评论
            if permalink and len(reviews) < self.max_items:
                try:
                    cr = req.get(f"https://www.reddit.com{permalink}.json",
                                 headers=headers, timeout=20)
                    cdata = cr.json()
                    if len(cdata) >= 2:
                        for c in cdata[1].get("data", {}).get("children", [])[:5]:
                            body = c.get("data", {}).get("body", "")
                            if len(body) >= 15:
                                reviews.append(self._make_review(
                                    user=c["data"].get("author"),
                                    rating=None, content=f"[Comment] {body[:400]}",
                                    created=c["data"].get("created_utc"),
                                    ups=c["data"].get("ups", 0),
                                ))
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

        return reviews

    async def _scrape_posts_only(self, product_name: str) -> list[dict]:
        """最后兜底: 只拿帖子"""
        import requests as req
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0"}
        try:
            resp = req.get("https://www.reddit.com/search.json",
                           params={"q": f"{product_name} review", "limit": 25},
                           headers=headers, timeout=30)
            data = resp.json()
        except Exception:
            return []

        reviews = []
        for item in data.get("data", {}).get("children", []):
            p = item.get("data", {})
            content = f"{p.get('title', '')}\n{p.get('selftext', '')}".strip()
            if len(content) >= 15:
                reviews.append(self._make_review(
                    user=p.get("author"), rating=None, content=content[:500],
                    created=p.get("created_utc"), ups=p.get("score", 0),
                ))
        return reviews

    def _make_review(self, user=None, rating=None, content="", created=None, ups=0):
        return {
            "platform": "reddit", "user": user or "anonymous", "rating": rating,
            "content": content,
            "time": datetime.fromtimestamp(created or time.time()).isoformat(),
            "upvotes": ups,
        }

    def _parse_crawl4ai(self, data) -> list[dict]:
        """解析 crawl4ai 返回 → 统一格式"""
        items = data if isinstance(data, list) else (
            json.loads(data) if isinstance(data, str) else [data])
        reviews = []
        for item in (items if isinstance(items, list) else [items])[:self.max_items]:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content") or item.get("text") or item.get("selftext") or "")
            if len(content) >= 10:
                reviews.append(self._make_review(
                    user=item.get("user") or item.get("author"),
                    content=content[:500],
                ))
        return reviews


# ═══════════════════════════════════════════════
# Amazon 爬虫
# ═══════════════════════════════════════════════

class AmazonScraper(BaseScraper):
    platform = "amazon"

    # 选择器集中管理 — Amazon改版时只改这里
    PRODUCT_LINK_SELS = [
        '[data-component-type="s-search-result"] h2 a',
        '.s-result-item[data-asin] h2 a',
        'a.a-link-normal.s-underline-text.s-link-style',
    ]
    REVIEW_CONTAINER_SELS = [
        '[data-hook="review"]', '.review.aok-relative',
        '#cm_cr-review_list .review', '.customer-review',
    ]
    USER_SELS = ['.a-profile-name', '[data-hook="review-author"]']
    RATING_SELS = ['[data-hook="review-star-rating"] .a-icon-alt', '.review-rating .a-icon-alt']
    CONTENT_SELS = ['[data-hook="review-body"]', '.review-text-content', '.review-data .review-text']
    DATE_SELS = ['[data-hook="review-date"]', '.review-date']

    async def _try_primary(self, product_name: str) -> list[dict]:
        """首选: crawl4ai"""
        try:
            from crawl4ai import AsyncWebCrawler 
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=f"https://www.amazon.com/s?k={product_name.replace(' ', '+')}",
                    extraction_strategy="Find the first product, go to its reviews, extract each review's author, star rating, text, and date."
                )
                if result and result.extracted_content:
                    items = result.extracted_content
                    items = items if isinstance(items, list) else json.loads(items) if isinstance(items, str) else [items]
                    return self._normalize_crawl4ai(items)
        except ImportError:
            pass
        except Exception as e:
            self._log(f"crawl4ai: {e}")
        return []

    async def _try_fallback(self, product_name: str) -> list[dict]:
        """备选: Playwright 真浏览器"""
        try:
            return await self._scrape_playwright(product_name)
        except ImportError:
            self._log("Playwright 未安装")
        except Exception as e:
            self._log(f"Playwright: {e}")
        return []

    async def _try_last_resort(self, product_name: str) -> list[dict]:
        """兜底: requests"""
        return await self._scrape_requests(product_name)

    async def _scrape_playwright(self, product_name: str) -> list[dict]:
        """Playwright: 搜 → 点 → 滚 → 提取"""
        from playwright.async_api import async_playwright  # type: ignore[import-untyped]

        reviews = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0",
                locale="en-US",
            )
            page = await ctx.new_page()

            try:
                await page.goto(
                    f"https://www.amazon.com/s?k={product_name.replace(' ', '+')}",
                    wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                if "Robot" in await page.title():
                    return []

                # 点第一个商品
                for sel in self.PRODUCT_LINK_SELS:
                    link = page.locator(sel).first
                    if await link.count() > 0:
                        await link.click()
                        await page.wait_for_timeout(4000)
                        break

                # 滚动到评论区
                for y in [800, 1500, 2500]:
                    await page.evaluate(f"window.scrollTo(0, {y})")
                    await page.wait_for_timeout(1000)

                # 找评论容器
                items = None
                for sel in self.REVIEW_CONTAINER_SELS:
                    items = page.locator(sel)
                    if await items.count() > 0:
                        break

                if items is None:
                    return []

                # 提取每条评论
                for i in range(min(await items.count(), self.max_items)):
                    try:
                        item = items.nth(i)
                        content = await self._extract_async(item, self.CONTENT_SELS)
                        if len(content) < 15:
                            continue
                        reviews.append({
                            "platform": "amazon",
                            "user": await self._extract_async(item, self.USER_SELS) or "anonymous",
                            "rating": self._parse_rating(await self._extract_async(item, self.RATING_SELS)),
                            "content": content[:500],
                            "time": (await self._extract_async(item, self.DATE_SELS)) or datetime.now().isoformat(),
                        })
                    except Exception:
                        continue
            finally:
                await browser.close()

        return reviews

    async def _scrape_requests(self, product_name: str) -> list[dict]:
        """requests: 只拿搜索结果页的评分预览"""
        import requests as req
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0",
                    "Accept-Language": "en-US,en;q=0.9"}
        try:
            resp = req.get("https://www.amazon.com/s",
                           params={"k": product_name}, headers=headers, timeout=30)
            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select('[data-component-type="s-search-result"]') or soup.select('.s-result-item[data-asin]')
        except Exception:
            return []

        reviews = []
        for card in cards[:self.max_items]:
            try:
                title = (card.select_one("h2 a span") or card.select_one("h2")).text.strip()
                rating_text = (card.select_one('.a-icon-star-small') or card.select_one('.a-icon-star'))
                rating_text = rating_text.text.strip() if rating_text else ""
                if title:
                    reviews.append({
                        "platform": "amazon", "user": "amazon_customer",
                        "rating": self._parse_rating(rating_text),
                        "content": f"{title} | 评分: {rating_text}"[:500],
                        "time": datetime.now().isoformat(),
                    })
            except Exception:
                continue
        return reviews

    async def _extract_async(self, item, selectors: list[str]) -> str:
        """Playwright 异步提取文本"""
        for sel in selectors:
            try:
                el = item.locator(sel).first
                if await el.count() > 0:
                    return (await el.inner_text()).strip()
            except Exception:
                continue
        return ""

    def _normalize_crawl4ai(self, items: list) -> list[dict]:
        reviews = []
        for item in (items or [])[:self.max_items]:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content") or item.get("text") or item.get("review") or "")
            if len(content) >= 10:
                reviews.append({
                    "platform": "amazon",
                    "user": str(item.get("user") or item.get("author") or "anonymous"),
                    "rating": self._parse_rating(item.get("rating") or item.get("stars")),
                    "content": content[:500],
                    "time": str(item.get("time") or item.get("date") or datetime.now().isoformat()),
                })
        return reviews

    @staticmethod
    def _parse_rating(text) -> Optional[float]:
        """'4.5 out of 5 stars' → 4.5"""
        import re
        if not text:
            return None
        m = re.search(r'(\d+\.?\d*)', str(text))
        if m:
            r = float(m.group(1))
            if 5 < r <= 10:
                r /= 2
            elif r > 10:
                r /= 20
            return round(max(1.0, min(5.0, r)), 1)
        return None


# ═══════════════════════════════════════════════
# B站 爬虫
# ═══════════════════════════════════════════════

class BilibiliScraper(BaseScraper):
    platform = "bilibili"

    async def _try_primary(self, product_name: str) -> list[dict]:
        """首选: crawl4ai"""
        try:
            from crawl4ai import AsyncWebCrawler 
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=f"https://search.bilibili.com/all?keyword={product_name.replace(' ', '%20')}",
                    extraction_strategy="Find video review results. For each: extract title, description, author, play count."
                )
                if result and result.extracted_content:
                    items = result.extracted_content
                    items = items if isinstance(items, list) else json.loads(items) if isinstance(items, str) else [items]
                    return self._normalize(items)
        except ImportError:
            pass
        except Exception as e:
            self._log(f"crawl4ai: {e}")
        return []

    async def _try_fallback(self, product_name: str) -> list[dict]:
        """备选: B站搜索API + 评论API"""
        return await self._scrape_api(product_name)

    async def _scrape_api(self, product_name: str) -> list[dict]:
        """requests: 搜索 → 视频列表 → 尝试拿评论"""
        import requests as req
        headers = {"User-Agent": "Mozilla/5.0 Chrome/126.0.0.0", "Referer": "https://www.bilibili.com/"}
        reviews = []

        for keyword in [f"{product_name} 评测", f"{product_name} 体验"]:
            try:
                sr = req.get("https://api.bilibili.com/x/web-interface/search/type",
                             params={"search_type": "video", "keyword": keyword},
                             headers=headers, timeout=30)
                for v in sr.json().get("data", {}).get("result", [])[:8]:
                    title = v.get("title", "").replace('<em class="keyword">', '').replace('</em>', '')
                    desc = v.get("description", "")
                    aid = v.get("aid") or v.get("id", 0)
                    content = f"{title} | {desc[:200]}" if desc else title

                    if len(content) >= 15:
                        reviews.append({
                            "platform": "bilibili", "user": v.get("author", "bilibili_user"),
                            "rating": None, "content": content[:500],
                            "time": datetime.fromtimestamp(v.get("pubdate", time.time())).isoformat(),
                            "play_count": v.get("play", 0),
                        })

                    # 尝试拿评论
                    if aid and len(reviews) < self.max_items:
                        try:
                            cr = req.get("https://api.bilibili.com/x/v2/reply/main",
                                         params={"oid": aid, "type": 1, "mode": 3, "ps": 5},
                                         headers=headers, timeout=15)
                            cdata = cr.json()
                            if cdata.get("code") == 0:
                                for c in cdata.get("data", {}).get("replies", [])[:3]:
                                    msg = c.get("content", {}).get("message", "")
                                    if len(msg) >= 10:
                                        reviews.append({
                                            "platform": "bilibili",
                                            "user": c.get("member", {}).get("uname", "bilibili_user"),
                                            "rating": None,
                                            "content": f"[Comment] {msg[:400]}",
                                            "time": datetime.fromtimestamp(c.get("ctime", time.time())).isoformat(),
                                        })
                            await asyncio.sleep(0.3)
                        except Exception:
                            pass
            except Exception as e:
                self._log(f"搜索 '{keyword}' 失败: {e}")
                continue

        return reviews

    def _normalize(self, items: list) -> list[dict]:
        reviews = []
        for item in (items or [])[:self.max_items]:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content") or item.get("text") or item.get("title") or "")
            if len(content) >= 10:
                reviews.append({
                    "platform": "bilibili",
                    "user": str(item.get("user") or item.get("author") or "bilibili_user"),
                    "rating": None, "content": content[:500],
                    "time": str(item.get("time") or datetime.now().isoformat()),
                })
        return reviews


# ═══════════════════════════════════════════════
# 京东 爬虫
# ═══════════════════════════════════════════════

class JDScraper(BaseScraper):
    platform = "jd"

    PRODUCT_LINK_SELS = [".gl-item a", ".goods-list-v2 .gl-item a"]
    COMMENT_TAB_SELS = ['li[data-anchor="#comment"]', 'text=商品评价']
    REVIEW_CONTAINER_SELS = ['.comment-item', '[class*="comment-item"]']
    USER_SELS = ['.nickname', '[class*="user"]', '[class*="nick"]']
    STAR_SELS = ['[class*="star"]', '.comment-star']
    CONTENT_SELS = ['.comment-con', '[class*="comment-con"]', '[class*="content"]']
    TIME_SELS = ['.time', '[class*="time"]', '[class*="date"]']

    async def _try_primary(self, product_name: str) -> list[dict]:
        """首选: Playwright 真浏览器 + 登录态"""
        return await self._scrape_playwright(product_name)

    async def _try_fallback(self, product_name: str) -> list[dict]:
        """备选: Playwright 无登录态再试一次"""
        return await self._scrape_playwright(product_name, load_state=False)

    async def _scrape_playwright(self, product_name: str, load_state: bool = True) -> list[dict]:
        """Playwright 京东专用"""
        from playwright.async_api import async_playwright  # type: ignore[import-untyped]

        reviews = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )

            # 尝试加载登录态
            if load_state and JD_STATE_FILE.exists():
                ctx = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    storage_state=str(JD_STATE_FILE),
                )
            else:
                ctx = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0",
                )

            page = await ctx.new_page()
            try:
                await page.goto(
                    f"https://search.jd.com/Search?keyword={product_name}&enc=utf-8",
                    wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                if "频控" in (await page.title()):
                    return []

                # 点第一个商品
                for sel in self.PRODUCT_LINK_SELS:
                    link = page.locator(sel).first
                    if await link.count() > 0:
                        await link.click()
                        await page.wait_for_timeout(5000)
                        break

                # 点评价tab
                await page.evaluate("window.scrollTo(0, 1200)")
                await page.wait_for_timeout(2000)
                for sel in self.COMMENT_TAB_SELS:
                    tab = page.locator(sel).first
                    if await tab.is_visible(timeout=2000):
                        await tab.click()
                        await page.wait_for_timeout(3000)
                        break

                # 提取评价
                items = None
                for sel in self.REVIEW_CONTAINER_SELS:
                    items = page.locator(sel)
                    if await items.count() > 0:
                        break

                if items is None:
                    return []

                for i in range(min(await items.count(), self.max_items)):
                    try:
                        item = items.nth(i)
                        user = await self._extract(item, self.USER_SELS)
                        star_cls = await self._extract(item, self.STAR_SELS, attr="class")
                        star = 3
                        for n in ["5", "4", "3", "2", "1"]:
                            if n in (star_cls or ""):
                                star = int(n)
                                break
                        content = await self._extract(item, self.CONTENT_SELS)
                        t = await self._extract(item, self.TIME_SELS)

                        if len(content) >= 5:
                            reviews.append({
                                "platform": "jd", "user": user or "匿名",
                                "rating": float(star), "content": content[:500],
                                "time": t or datetime.now().isoformat(),
                            })
                    except Exception:
                        continue
            finally:
                await browser.close()

        return reviews

    async def _extract(self, item, selectors: list[str], attr: str = "text") -> str:
        """Playwright 异步提取"""
        for sel in selectors:
            try:
                el = item.locator(sel).first
                if await el.count() > 0:
                    if attr == "class":
                        return await el.get_attribute("class") or ""
                    return (await el.inner_text()).strip()
            except Exception:
                continue
        return ""


# ═══════════════════════════════════════════════
# 小红书 — 开闭原则预留
# ═══════════════════════════════════════════════

class XiaohongshuScraper(BaseScraper):
    platform = "xiaohongshu"

    async def _try_primary(self, product_name: str) -> list[dict]:
        return []  # MVP阶段跳过

    async def _try_fallback(self, product_name: str) -> list[dict]:
        return []


# ═══════════════════════════════════════════════
# 爬虫注册表 + 调度入口
# ═══════════════════════════════════════════════

# 平台 → Scraper类 的映射（开闭原则：加平台=在这里加一行）
SCRAPER_REGISTRY = {
    "reddit": RedditScraper,
    "amazon": AmazonScraper,
    "bilibili": BilibiliScraper,
    "jd": JDScraper,
    "xiaohongshu": XiaohongshuScraper,
}


async def scrape_reviews(product_name: str, platforms: list[str]) -> dict[str, list[dict]]:
    """
    爬虫主入口 — 真正异步并行
    用法: reviews = await scrape_reviews("Soundcore Liberty 5 Pro", ["reddit", "amazon"])

    返回: {platform: [review_dict, ...], ...}
    """
    # 过滤掉未启用的平台
    active = [p for p in platforms if p in PLATFORMS and PLATFORMS[p]["enabled"]]
    if not active:
        return {}

    # ── 真正并行：所有平台同时启动 ──
    async def _scrape_one(platform: str) -> tuple[str, list[dict]]:
        scraper_cls = SCRAPER_REGISTRY.get(platform)
        if scraper_cls is None:
            return platform, []
        scraper = scraper_cls()
        reviews = await scraper.scrape(product_name)
        scraper._save_raw(product_name, reviews)
        return platform, reviews

    tasks = [_scrape_one(p) for p in active]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 组装结果
    output = {}
    for result in results:
        if isinstance(result, Exception):
            try:
                print(f"  [scraper] crawl error: {result}")
            except UnicodeEncodeError:
                safe = str(result).encode("utf-8", errors="replace").decode("utf-8", errors="replace")
                print(f"  [scraper] crawl error: {safe}")
            continue
        platform, reviews = result
        output[platform] = reviews

    return output

"""
================================================================
重试装饰器
================================================================
职责: 给函数加自动重试能力，指数退避
负责人: 朱子钦
依赖: 无（纯工具）
被依赖: engine/scraper.py, agents/base.py 等需要网络调用的模块

用法:
  @retry(max_attempts=3, delay=2.0)
  def call_api():
      ...

  第1次失败 → 等2秒 → 第2次失败 → 等4秒 → 第3次失败 → 抛异常
================================================================
"""
import time
import functools


def retry(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """失败自动重试，指数退避"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if attempt < max_attempts - 1:
                        wait = delay * (backoff ** attempt)
                        try:
                            print(f"  [retry] Attempt {attempt+1} failed: {e}, retry in {wait:.0f}s...")
                        except UnicodeEncodeError:
                            safe = str(e).encode("utf-8", errors="replace").decode("utf-8", errors="replace")
                            print(f"  [retry] Attempt {attempt+1} failed: {safe}, retry in {wait:.0f}s...")
                        time.sleep(wait)
            raise last_err
        return wrapper
    return decorator

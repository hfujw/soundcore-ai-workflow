"""
================================================================
全局配置文件
================================================================
职责: 集中管理所有常量、路径、API配置
负责人: 朱子钦
依赖: 无（最底层的文件，被所有人 import）
被哪些文件依赖: 几乎全部文件都 import config

注意:
  - API Key 不写在这里，从环境变量读取（.env文件）
  - 本地敏感的配置放在 local_config.py（Git忽略）
================================================================
"""
import os
from pathlib import Path

# ── 项目根目录 ──
# backend/config.py → backend/ → 项目根目录
ROOT = Path(__file__).parent.parent
BACKEND = Path(__file__).parent
DATA = ROOT / "data"
FRONTEND = ROOT / "frontend" / "src"

# ── 数据存储路径 ──
DATA_RAW = DATA / "raw"           # 爬虫原始JSON
DATA_CLEANED = DATA / "cleaned"   # 清洗后统一格式JSON
DATA_REPORTS = DATA / "reports"   # 最终Markdown报告
DATA_STATES = DATA / "states"     # 浏览器登录态（京东cookie等）

# ── Prompt 模板路径 ──
PROMPTS_DIR = BACKEND / "prompts"

# ── DeepSeek API ──
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TEMPERATURE = 0.3
DEEPSEEK_MAX_TOKENS = 4096
DEEPSEEK_TIMEOUT = 120  # 秒

# ── 4个 Agent 的显示信息 ──
AGENTS = {
    "super_brain":       {"name": "超级智囊",   "emoji": "🔍", "desc": "多平台评价抓取与洞察提取"},
    "user_avatar":       {"name": "用户替身",   "emoji": "👤", "desc": "4类用户画像构建与压力测试"},
    "competitor_scout":  {"name": "竞品侦察兵", "emoji": "🕵️", "desc": "竞品参数对比与机会发现"},
    "industry_expert":   {"name": "行业专家",   "emoji": "🧠", "desc": "技术可行性与商业评估"},
}

# ── 预设产品列表 ──
PRESET_PRODUCTS = [
    "Soundcore Liberty 5 Pro",
    "Soundcore Liberty 5 Pro Max",
    "Soundcore AeroFit 2",
    "Soundcore AeroFit Pro",
    "Soundcore Liberty 4 NC",
]

# ── 可用平台 ──
PLATFORMS = {
    "reddit":      {"name": "Reddit",     "enabled": True},
    "amazon":      {"name": "Amazon",     "enabled": True},
    "bilibili":    {"name": "B站",         "enabled": True},
    "jd":          {"name": "京东",       "enabled": True},
    "xiaohongshu": {"name": "小红书",     "enabled": False},  # MVP跳过，遵循开闭原则
}

# ── 竞品列表（竞品侦察兵Agent使用）─
COMPETITORS = [
    {"name": "AirPods Pro 2",              "brand": "Apple"},
    {"name": "WF-1000XM5",                 "brand": "Sony"},
    {"name": "FreeBuds Pro 4",             "brand": "Huawei"},
    {"name": "QuietComfort Ultra Earbuds", "brand": "Bose"},
]

# ── 爬虫参数 ──
MAX_REVIEWS_PER_PLATFORM = 50   # 每个平台最多取多少条
MAX_REVIEWS_FOR_LLM = 120       # 喂给LLM的条数上限（DeepSeek 128K够用）
CRAWL_DELAY_SECONDS = 2         # 爬取间隔

# ── 京东特有配置 ──
JD_STATE_FILE = DATA_STATES / "jd_state.json"  # Playwright登录态文件

# ── 确保目录存在（首次运行时自动创建）─
for d in [DATA_RAW, DATA_CLEANED, DATA_REPORTS, DATA_STATES]:
    d.mkdir(parents=True, exist_ok=True)


# ── 尝试加载本地敏感配置（Git忽略，每个人自己的）─
try:
    from backend.local_config import *  # noqa: F403
except ImportError:
    pass  # 没有 local_config.py 就用默认值

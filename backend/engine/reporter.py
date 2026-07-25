"""
================================================================
报告生成模块
================================================================
职责: 把4个Agent的输出 + 数据统计 → 拼接成完整 Markdown 报告
负责人: 朱子钦
依赖: config.py
被依赖: routers/pipeline.py

报告结构（固定模板）:
  1. 头部（产品名 + 生成时间 + 数据来源 + 免责声明）
  2. 第一章：用户洞察报告（Agent1输出）
  3. 第二章：产品概念定义（Agent2输出）
  4. 第三章：竞品机会图谱（Agent3输出）
  5. 第四章：可行性评估（Agent4输出）
  6. 附录（数据声明 + AI角色说明 + 方法对比）

核心函数:
  generate_report(product, stats, agent_outputs) → str（文件路径）

TODO: 此文件目前为骨架，具体报告模板待实现
================================================================
"""
from datetime import datetime
from config import DATA_REPORTS


def generate_report(
    product_name: str,
    stats: dict,
    agent_outputs: dict[str, dict],
) -> str:
    """
    生成完整 Markdown 报告

    Args:
        product_name:  产品名
        stats:         get_stats() 的输出（总数、平台分布、平均分等）
        agent_outputs: 4个Agent的输出 {
                         "super_brain":      {"raw_output": "..."},
                         "user_avatar":      {"raw_output": "..."},
                         "competitor_scout": {"raw_output": "..."},
                         "industry_expert":  {"raw_output": "..."},
                       }

    Returns:
        报告文件路径
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    sb = agent_outputs.get("super_brain", {}).get("raw_output", "暂无分析结果")
    ua = agent_outputs.get("user_avatar", {}).get("raw_output", "暂无分析结果")
    cs = agent_outputs.get("competitor_scout", {}).get("raw_output", "暂无分析结果")
    ie = agent_outputs.get("industry_expert", {}).get("raw_output", "暂无分析结果")

    platform_desc = "、".join([f"{p}({c}条)" for p, c in stats.get("platforms", {}).items()])

    report = f"""# {product_name} 产品洞察报告

> 📅 生成时间: {now}
> 📊 数据来源: {platform_desc or '无'}
> 🤖 分析引擎: AI超级智囊 + AI用户替身 + AI竞品侦察兵 + AI行业专家
> 📈 总评价数: {stats.get("total", 0)} | 平均评分: {stats.get("avg_rating", "N/A")}
> 🌍 语言分布: 中文 {stats.get("language", {}).get("zh", 0)} / 英文 {stats.get("language", {}).get("en", 0)}

---

## 第一章：用户洞察报告

> 🤖 分析者：AI超级智囊

{sb}

---

## 第二章：产品概念定义

> 🤖 分析者：AI用户替身

{ua}

---

## 第三章：竞品机会图谱

> 🤖 分析者：AI竞品侦察兵

{cs}

---

## 第四章：可行性评估

> 🤖 分析者：AI行业专家

{ie}

---

## 附录

### A. 数据来源声明
本报告基于以下平台的真实用户评价分析生成：
{platform_desc or '暂无数据'}

### B. AI角色分工说明
| 角色 | 职责 |
|------|------|
| 🔍 超级智囊 | 多平台评价抓取、痛点提取、满意度评分 |
| 👤 用户替身 | 用户画像构建、压力测试、功能优先级排序 |
| 🕵️ 竞品侦察兵 | 竞品参数对比、口碑追踪、机会发现 |
| 🧠 行业专家 | 技术可行性、供应链评估、商业建议 |

---

> 🤖 本报告由 AI原生产品设计工作流 自动生成
> 生成时间: {now}
"""
    safe_name = product_name.replace(" ", "_").replace("/", "_")
    fname = DATA_REPORTS / f"{safe_name}_{timestamp}.md"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(report)

    return str(fname)

"""
================================================================
Agent 3: AI竞品侦察兵 — 竞争情报
================================================================
职责: 对比4大竞品，找到"用户想要但竞品都没做"的空白机会
负责人: 同学
依赖: agents/base.py, config.py（COMPETITORS 竞品列表）
被依赖: agents/industry_expert.py (Agent4需要它的机会图谱)

输入: {
  "super_brain_output": Agent1的输出,
  "reviews": [...统一格式评价...],
  "product": "Soundcore Liberty 5 Pro Max"
}

特殊处理: 从所有原始评价中提取涉及竞品关键词的原话
  关键词: AirPods, 索尼, Sony, 华为, Huawei, Bose, XM5, FreeBuds
  只提取提及了竞品的评价 → 作为"用户竞品对比原话"输入

输出: {
  "agent": "competitor_scout",
  "raw_output": "## 核心参数对比矩阵\n...",
  "timestamp": "2026-07-26T15:30:00"
}

执行时机: Phase 1（与超级智囊并行）
================================================================
"""
import json
from agents.base import BaseAgent
from config import COMPETITORS


class CompetitorScout(BaseAgent):
    name = "competitor_scout"
    display_name = "竞品侦察兵"
    emoji = "🕵️"
    prompt_file = "competitor_scout.txt"

    def build_message(self, input_data: dict) -> str:
        """构建消息：Agent1输出 + 竞品参数 + 用户竞品对比原话"""
        sb = input_data.get("super_brain_output", {})
        product = input_data.get("product", "未知产品")
        reviews = input_data.get("reviews", [])

        # 从评价中提取涉及竞品对比的原话
        competitor_kw = ["AirPods", "airpods", "索尼", "Sony", "华为", "Huawei",
                         "Bose", "bose", "苹果", "Apple", "XM5", "FreeBuds"]
        comparison_lines = []
        for r in reviews:
            content = r.get("content", "")
            if any(kw in content for kw in competitor_kw):
                comparison_lines.append(f"[{r['platform']}] {r['user']}: {content[:200]}")

        sb_text = sb.get("raw_output", "") if sb else "暂无超级智囊分析结果"

        return f"""## 分析任务

**产品**: {product}

## 竞品列表（已知参数）
{json.dumps(COMPETITORS, ensure_ascii=False, indent=2)}

## 超级智囊的用户洞察（完整输出）

{sb_text}

## 用户评价中的竞品对比原话（{len(comparison_lines)}条）

{chr(10).join(comparison_lines[:40])}

## 请按 System Prompt 要求输出竞品机会图谱"""

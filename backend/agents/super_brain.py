"""
================================================================
Agent 1: AI超级智囊 — 用户洞察
================================================================
职责: 从统一格式的评价数据中提取结构化用户洞察
负责人: 同学
依赖: agents/base.py, utils/llm.py
被依赖: agents/user_avatar.py, agents/industry_expert.py (Agent2和Agent4需要它的输出)

输入: {
  "reviews": [...统一格式评价...],  # 最多120条
  "product": "Soundcore Liberty 5 Pro Max",
  "stats":   {...数据统计...}       # normalizer.get_stats() 的输出
}

输出: {
  "agent": "super_brain",
  "raw_output": "## 高频痛点Top10\n1. ...",  # LLM原始输出（Markdown）
  "timestamp": "2026-07-26T15:30:00"
}

执行时机: Phase 1（与竞品侦察兵并行）
================================================================
"""
import json
from agents.base import BaseAgent


class SuperBrain(BaseAgent):
    name = "super_brain"
    display_name = "超级智囊"
    emoji = "🔍"
    prompt_file = "super_brain.txt"

    def build_message(self, input_data: dict) -> str:
        """
        构建 User Message：把评价列表编号后喂给LLM

        输入量估算：
          120条 × 200字/条 = 24000字
          + stats JSON ~500字
          + 指令 ~500字
          = 25000字 ≈ 15000 tokens
          DeepSeek 128K 上下文 → 完全够用
        """
        reviews = input_data.get("reviews", [])
        product = input_data.get("product", "未知产品")
        stats = input_data.get("stats", {})

        # 逐条编号
        review_lines = []
        for i, r in enumerate(reviews, 1):
            rating_str = f"⭐{r['rating']}" if r['rating'] else "无评分"
            line = (f"[{i}] [{r['platform']}] {rating_str} | {r['user'][:12]} | "
                    f"{r['content'][:200]}")
            review_lines.append(line)

        reviews_text = "\n".join(review_lines)

        return f"""## 分析任务

**产品**: {product}
**数据概览**: {json.dumps(stats, ensure_ascii=False)}

## 用户评价数据（共{len(reviews)}条）

{reviews_text}

## 请按 System Prompt 要求输出分析结果"""

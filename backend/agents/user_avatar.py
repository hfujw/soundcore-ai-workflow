"""
================================================================
Agent 2: AI用户替身 — 产品概念验证
================================================================
职责: 基于Agent1的痛点构建4类用户画像，对功能提案做压力测试
负责人: 同学
依赖: agents/base.py（不直接依赖Agent1，通过input_data接收Agent1的输出）
被依赖: agents/industry_expert.py (Agent4需要它的优先级矩阵)

输入: {
  "super_brain_output": {"raw_output": "Agent1的完整输出", ...},
  "product": "Soundcore Liberty 5 Pro Max"
}

输出: {
  "agent": "user_avatar",
  "raw_output": "## 需求排序表\n| 功能 | 通勤族 | 办公族 | ...",
  "timestamp": "2026-07-26T15:30:30"
}

执行时机: Phase 2（与行业专家并行，但需要等Agent1先完成）

重要: Agent1完整输出全量喂入，不截断
  Agent1的输出约4000字 → 完全不需要截断
================================================================
"""
from agents.base import BaseAgent


class UserAvatar(BaseAgent):
    name = "user_avatar"
    display_name = "用户替身"
    emoji = "👤"
    prompt_file = "user_avatar.txt"

    def build_message(self, input_data: dict) -> str:
        """把Agent1的输出全量喂给Agent2做压力测试"""
        sb = input_data.get("super_brain_output", {})
        product = input_data.get("product", "未知产品")
        pain_points_text = sb.get("raw_output", "暂无超级智囊分析结果")

        return f"""## 分析任务

**产品**: {product}

## 超级智囊的用户洞察结果（完整输出，未截断）

{pain_points_text}

## 请按 System Prompt 要求：
1. 基于4类用户画像做压力测试
2. 生成功能优先级矩阵（P0/P1/P2/P3）
3. 给出P0功能的交互方案建议"""

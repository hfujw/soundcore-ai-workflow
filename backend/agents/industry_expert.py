"""
================================================================
Agent 4: AI行业专家 — 可行性评估
================================================================
职责: 综合前三个Agent的输出，做技术/供应链/商业三维评估
负责人: 同学
依赖: agents/base.py（不直接依赖前三个Agent，通过input_data接收）
被依赖: engine/reporter.py（报告生成器拼接它的输出）

输入: {
  "super_brain_output":      Agent1输出,
  "user_avatar_output":      Agent2输出,
  "competitor_scout_output": Agent3输出,
  "product": "Soundcore Liberty 5 Pro Max"
}

输入量估算:
  Agent1输出 ~4000字 + Agent2输出 ~3000字 + Agent3输出 ~3000字
  = 10000字，完全不需要截断

输出: {
  "agent": "industry_expert",
  "raw_output": "## 技术可行性评估\n...",
  "timestamp": "2026-07-26T15:31:00"
}

执行时机: Phase 2（与用户替身并行，但实际LLM调用需要等Agent2完成）
================================================================
"""
from agents.base import BaseAgent


class IndustryExpert(BaseAgent):
    name = "industry_expert"
    display_name = "行业专家"
    emoji = "🧠"
    prompt_file = "industry_expert.txt"

    def build_message(self, input_data: dict) -> str:
        """把前三个Agent的全部输出全量喂给Agent4"""
        sb = input_data.get("super_brain_output", {}).get("raw_output", "暂无")
        ua = input_data.get("user_avatar_output", {}).get("raw_output", "暂无")
        cs = input_data.get("competitor_scout_output", {}).get("raw_output", "暂无")
        product = input_data.get("product", "未知产品")

        return f"""## 可行性评估任务

**产品**: {product}

## 前置分析结果（完整输出，未截断）

### 超级智囊（用户洞察）
{sb}

### 用户替身（功能优先级）
{ua}

### 竞品侦察兵（机会图谱）
{cs}

## 请按 System Prompt 要求：
1. 对P0/P1功能做技术可行性评分（芯片算力/软件复杂度/供应链风险/工期）
2. 分析工程矛盾（降噪vs舒适、续航vs重量）
3. 给出商业评估（定价+销量预测+AI策略建议）
4. 风险预警（Top3风险）"""

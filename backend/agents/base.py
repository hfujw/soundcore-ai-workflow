"""
================================================================
Agent 基类
================================================================
职责: 所有4个 AI Agent 的父类，提供通用功能
负责人: 同学
依赖: utils/llm.py, config.py
被依赖: 4个Agent子类

核心方法:
  _load_prompt()      → 从 prompts/ 读取 System Prompt
  build_message(data) → 构建 User Message（子类必须实现）
  parse_response(raw) → 解析 LLM 原始回复（子类可重写）
  analyze(data)       → 完整的"调LLM分析"流程

设计原则:
  - 每个Agent只实现 build_message()，其余从基类继承
  - System Prompt 存于独立 .txt 文件，改Prompt不用改代码
  - 输入全量喂入，不截断（DeepSeek 128K完全够用）
================================================================
"""
from pathlib import Path
from config import PROMPTS_DIR
from utils.llm import ask_deepseek
from datetime import datetime


class BaseAgent:
    """AI Agent 基类"""

    # ── 子类必须覆盖这些属性 ──
    name: str = "base"              # 内部代号
    display_name: str = "基础Agent"  # UI显示名称
    emoji: str = "🤖"               # UI表情
    prompt_file: str = ""           # prompts/ 下的文件名，如 "super_brain.txt"

    def __init__(self):
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """从文件加载 System Prompt"""
        prompt_path = PROMPTS_DIR / self.prompt_file
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        print(f"  ⚠️ Prompt文件不存在: {prompt_path}")
        return "你是一个专业的分析助手。"

    def analyze(self, input_data: dict) -> dict:
        """
        核心分析方法 — 完整的"调LLM分析"流程
        子类不需要重写这个方法，只需实现 build_message()

        Args:
            input_data: 子类 build_message() 需要的输入数据

        Returns:
            {"agent": self.name, "raw_output": "...", "timestamp": "..."}
        """
        user_message = self.build_message(input_data)
        raw_response = ask_deepseek(self.system_prompt, user_message)
        return {
            "agent": self.name,
            "raw_output": raw_response,
            "timestamp": datetime.now().isoformat(),
        }

    def build_message(self, input_data: dict) -> str:
        """
        构建发送给 LLM 的 User Message
        每个 Agent 子类必须实现自己的版本
        """
        raise NotImplementedError("子类必须实现 build_message()")

    def summary(self) -> dict:
        """返回 Agent 的显示信息（给UI用）"""
        return {
            "agent_id": self.name,
            "name": self.display_name,
            "emoji": self.emoji,
        }

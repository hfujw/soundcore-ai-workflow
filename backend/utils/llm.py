"""
================================================================
DeepSeek LLM 调用封装
================================================================
职责: 封装 DeepSeek API 调用，输入 prompt 输出文本
负责人: 朱子钦
依赖: requests, config.py（DEEPSEEK_API_KEY等配置）
被依赖: agents/base.py（所有Agent通过基类调用它）

核心函数:
  ask_deepseek(system_prompt, user_message) → str
  ask_deepseek_stream(system_prompt, user_message) → Generator[str]
    (流式版本，给WebSocket实时推送用)

设计原则:
  - 不引入 LangChain（过度设计，10行代码的事）
  - 直接调 HTTP API（代码全透明，好调试）
  - 超时120秒，由调用方决定是否重试
================================================================
"""
import json
import requests
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL, DEEPSEEK_TEMPERATURE, DEEPSEEK_MAX_TOKENS, DEEPSEEK_TIMEOUT
)


def ask_deepseek(
    system_prompt: str,
    user_message: str,
    temperature: float = None,
    max_tokens: int = None,
) -> str:
    """
    调用 DeepSeek Chat API，返回完整文本回复

    Args:
        system_prompt: 系统提示词（定义AI角色和行为）
        user_message:  用户消息（要分析的数据）
        temperature:   创造性参数，0=保守 1=随机，默认用config值
        max_tokens:    最大输出长度，默认用config值

    Returns:
        LLM的文本回复

    Raises:
        requests.RequestException: 网络层错误
        KeyError:                  API返回格式异常
    """
    resp = requests.post(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature or DEEPSEEK_TEMPERATURE,
            "max_tokens": max_tokens or DEEPSEEK_MAX_TOKENS,
        },
        timeout=DEEPSEEK_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def ask_deepseek_stream(system_prompt: str, user_message: str):
    """
    流式调用 DeepSeek — 边生成边返回

    用途: 给 WebSocket 推送给前端，实现"AI正在思考..."的实时文字流
    用法: for chunk in ask_deepseek_stream(sys, usr): websocket.send(chunk)
    """
    resp = requests.post(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": DEEPSEEK_TEMPERATURE,
            "max_tokens": DEEPSEEK_MAX_TOKENS,
            "stream": True,
        },
        timeout=DEEPSEEK_TIMEOUT,
        stream=True,
    )
    for line in resp.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
                except json.JSONDecodeError:
                    continue

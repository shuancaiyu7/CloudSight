from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMSettings:
    base_url: str
    api_key: str
    model: str


def load_settings(secrets: dict | None = None) -> LLMSettings:
    secrets = secrets or {}
    return LLMSettings(
        base_url=secrets.get("LLM_BASE_URL") or os.getenv("LLM_BASE_URL", "https://jojocode.com/v1"),
        api_key=secrets.get("LLM_API_KEY") or os.getenv("LLM_API_KEY", ""),
        model=secrets.get("LLM_MODEL") or os.getenv("LLM_MODEL", "gpt-5.6-terra"),
    )


def generate_report(
    settings: LLMSettings, question: str, evidence: list[dict], tool_result: dict
) -> dict:
    if not settings.api_key:
        raise RuntimeError("尚未配置 LLM_API_KEY，将使用本地安全降级报告。")

    from openai import OpenAI

    prompt = {
        "任务": "你是云服务故障初检助手。只能根据证据给建议，不可声称执行过真实命令。",
        "用户问题": question,
        "资料证据": evidence,
        "模拟工具结果": tool_result,
        "输出格式": {
            "summary": "现象简述",
            "risk_level": "低/中/高",
            "possible_causes": ["最多三项，有证据才写"],
            "steps": ["按安全顺序给出三到五步"],
            "solutions": ["二到四项解决建议；只给出需人工确认的安全方案，不可声称执行过操作"],
            "human_handoff": True,
            "citations": [{"source": "资料名", "excerpt": "引用摘要"}],
        },
    }
    client = OpenAI(base_url=settings.base_url.rstrip("/"), api_key=settings.api_key)
    response = client.chat.completions.create(
        model=settings.model,
        messages=[
            {
                "role": "system",
                "content": "只返回合法 JSON，不使用 Markdown 代码块。",
            },
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        temperature=0.2,
        timeout=35,
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content.removeprefix("```json").removesuffix("```").strip())

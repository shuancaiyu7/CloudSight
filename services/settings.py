from __future__ import annotations

from collections.abc import Callable, Mapping


def safe_secret_mapping(secret_loader: Callable[[], Mapping]) -> dict:
    """允许本地演示在没有 secrets.toml 时进入模型降级流程。"""
    try:
        return dict(secret_loader())
    except Exception:  # Streamlit 在没有密钥文件时会抛出专用异常。
        return {}

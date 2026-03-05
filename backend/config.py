# -*- coding: utf-8 -*-
"""
部署环境变量统一配置：安全读取、类型转换与默认值。
在 Vercel / Render / Streamlit 等平台配置 Environment Variables 后，由此模块读取。
"""
import os
import re


def _env(key: str, default: str = "") -> str:
    """读取环境变量，返回去除首尾空白的字符串。"""
    return (os.environ.get(key) or default).strip()


def _env_int(key: str, default: int) -> int:
    """读取整型环境变量，非法值时回退为默认值。"""
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    """读取布尔型环境变量。支持 1/0, true/false, yes/no（不区分大小写）。"""
    v = (os.environ.get(key) or "").strip().lower()
    if v in ("1", "true", "yes"):
        return True
    if v in ("0", "false", "no"):
        return False
    return default


def _safe_path(value: str, default: str) -> str:
    """简单路径校验：禁止 '..' 与绝对路径，避免路径穿越。"""
    if not value:
        return default
    # 禁止父目录与绝对路径（按平台）
    if ".." in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return default
    return value


# ---------------------------------------------------------------------------
# 对外配置（仅通过以下常量使用，不要在 app 里直接读 os.environ）
# ---------------------------------------------------------------------------

# 服务监听端口（Vercel/Render/Streamlit 等会注入 PORT）
PORT = _env_int("PORT", 5000)

# 是否开启 Flask 调试（生产务必为 False）
FLASK_DEBUG = _env_bool("FLASK_DEBUG", False)

# 上传与输出目录（相对路径，禁止 .. 与绝对路径）
UPLOAD_FOLDER = _safe_path(_env("UPLOAD_FOLDER", "uploads"), "uploads")
OUTPUT_FOLDER = _safe_path(_env("OUTPUT_FOLDER", "outputs"), "outputs")

# 最大上传体积（MB）。平台限制较小时可在环境变量中调小（如 100）
MAX_CONTENT_LENGTH_MB = max(1, min(500, _env_int("MAX_CONTENT_LENGTH_MB", 500)))
MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH_MB * 1024 * 1024

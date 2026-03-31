#!/usr/bin/env python3
"""
配置管理

敏感信息通过环境变量配置，放入 .env 文件
"""
import os
from typing import List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Secret:
    """
    敏感配置封装

    延迟获取环境变量，避免在导入时暴露
    """
    def __init__(self, key: str, default: str = ""):
        self._key = key
        self._default = default

    def get(self) -> str:
        """获取配置值"""
        return os.getenv(self._key, self._default)

    def __str__(self) -> str:
        return "***"

    def __repr__(self) -> str:
        return f"Secret({self._key})"


# ==================== OKX API ====================
OKX_API_KEY = Secret("OKX_API_KEY")
OKX_SECRET = Secret("OKX_SECRET")
OKX_PASSPHRASE = Secret("OKX_PASSPHRASE")

# ==================== 通知渠道配置 ====================

# 企业微信机器人（推荐）
WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK", "")

# Server酱（微信推送）
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY", "")

# Qmsg酱（QQ消息）
QMSG_KEY = os.getenv("QMSG_KEY", "")
QMSG_QQ = os.getenv("QMSG_QQ", "")

# 钉钉机器人
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")

# Gmail 邮件通知
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_TO = os.getenv("GMAIL_TO", "")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ==================== 监控参数 ====================

# 持仓跌幅告警阈值（不含杠杆）
POSITION_LOSS_THRESHOLD = float(os.getenv("POSITION_LOSS_THRESHOLD", "0.01"))

# 监控频率（秒）
PRICE_CHECK_INTERVAL = int(os.getenv("PRICE_CHECK_INTERVAL", "60"))
POSITION_CHECK_INTERVAL = int(os.getenv("POSITION_CHECK_INTERVAL", "30"))
ORDER_CHECK_INTERVAL = int(os.getenv("ORDER_CHECK_INTERVAL", "10"))
SIGNAL_CHECK_INTERVAL = int(os.getenv("SIGNAL_CHECK_INTERVAL", "300"))

# 金叉死叉参数
EMA_FAST_PERIOD = int(os.getenv("EMA_FAST_PERIOD", "12"))
EMA_SLOW_PERIOD = int(os.getenv("EMA_SLOW_PERIOD", "26"))

# 形态识别参数
PATTERN_LOOKBACK = int(os.getenv("PATTERN_LOOKBACK", "20"))

# 监控的交易对（留空则监控全部）
WATCH_SYMBOLS: List[str] = [
    s.strip() for s in os.getenv("WATCH_SYMBOLS", "").split(",") if s.strip()
]

# 排除的交易对
EXCLUDE_SYMBOLS: List[str] = [
    s.strip() for s in os.getenv("EXCLUDE_SYMBOLS", "").split(",") if s.strip()
]

# ==================== 功能开关 ====================

ENABLE_POSITION_MONITOR = os.getenv("ENABLE_POSITION_MONITOR", "true").lower() == "true"
ENABLE_ORDER_MONITOR = os.getenv("ENABLE_ORDER_MONITOR", "true").lower() == "true"
ENABLE_SIGNAL_MONITOR = os.getenv("ENABLE_SIGNAL_MONITOR", "true").lower() == "true"

# 通知开关
NOTIFY_POSITION_LOSS = os.getenv("NOTIFY_POSITION_LOSS", "true").lower() == "true"
NOTIFY_ORDER_FILLED = os.getenv("NOTIFY_ORDER_FILLED", "true").lower() == "true"
NOTIFY_GOLDEN_CROSS = os.getenv("NOTIFY_GOLDEN_CROSS", "true").lower() == "true"
NOTIFY_DEATH_CROSS = os.getenv("NOTIFY_DEATH_CROSS", "true").lower() == "true"
NOTIFY_PATTERN_UPTREND = os.getenv("NOTIFY_PATTERN_UPTREND", "true").lower() == "true"

# 通知冷却时间（秒）- 防止重复通知
NOTIFY_COOLDOWN = int(os.getenv("NOTIFY_COOLDOWN", "300"))


def get_okx_credentials() -> dict:
    """获取 OKX 凭证"""
    return {
        "api_key": OKX_API_KEY.get(),
        "secret": OKX_SECRET.get(),
        "passphrase": OKX_PASSPHRASE.get(),
    }

#!/usr/bin/env python3
"""
Qmsg酱通知（QQ消息推送）
"""
import logging
import requests

from .base import BaseNotifier, NotifyMessage, NotifyLevel

logger = logging.getLogger(__name__)


class QmsgNotifier(BaseNotifier):
    """
    Qmsg酱推送 (QQ 消息)

    使用方法:
    1. 访问 https://qmsg.zendee.cn/ 获取 Key
    2. 配置到 .env:
       QMSG_KEY=xxx
       QMSG_QQ=你的QQ号
    """

    API_URL = "https://qmsg.zendee.cn/send"

    def __init__(self, key: str, qq: str = ""):
        self.key = key
        self.qq = qq

    def is_configured(self) -> bool:
        return bool(self.key)

    def send(self, message: NotifyMessage) -> bool:
        """发送消息"""
        if not self.key:
            logger.warning("[Qmsg] Key 未配置")
            return False

        try:
            # 构建消息内容
            level_emoji = {
                NotifyLevel.INFO: "📢",
                NotifyLevel.WARNING: "⚠️",
                NotifyLevel.ERROR: "❌",
                NotifyLevel.CRITICAL: "🚨"
            }
            emoji = level_emoji.get(message.level, "📢")

            content = f"""{emoji} {message.title}

时间: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"""

            if message.symbol:
                content += f"\n交易对: {message.symbol}"

            content += f"\n\n{message.content}"

            params = {
                "key": self.key,
                "msg": content
            }

            if self.qq:
                params["qq"] = self.qq

            response = requests.get(
                self.API_URL,
                params=params,
                timeout=10
            )

            result = response.json()
            if result.get("success"):
                logger.info(f"[Qmsg] 发送成功: {message.title}")
                return True
            else:
                logger.error(f"[Qmsg] 发送失败: {result}")
                return False

        except Exception as e:
            logger.error(f"[Qmsg] 发送异常: {e}")
            return False

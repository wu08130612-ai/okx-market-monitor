#!/usr/bin/env python3
"""
Server酱通知（微信推送）
"""
import logging
import requests

from .base import BaseNotifier, NotifyMessage

logger = logging.getLogger(__name__)


class ServerChanNotifier(BaseNotifier):
    """
    Server酱推送 (微信服务号推送)

    使用方法:
    1. 访问 https://sct.ftqq.com/ 获取 SendKey
    2. 配置到 .env: SERVERCHAN_KEY=SCTxxx
    """

    def __init__(self, send_key: str):
        self.send_key = send_key
        self.api_url = f"https://sctapi.ftqq.com/{send_key}.send"

    def is_configured(self) -> bool:
        return bool(self.send_key)

    def send(self, message: NotifyMessage) -> bool:
        """发送消息"""
        if not self.send_key:
            logger.warning("[Server酱] SendKey 未配置")
            return False

        try:
            payload = {
                "title": message.title,
                "desp": message.content
            }

            response = requests.post(
                self.api_url,
                data=payload,
                timeout=10
            )

            result = response.json()
            if result.get("code") == 0:
                logger.info(f"[Server酱] 发送成功: {message.title}")
                return True
            else:
                logger.error(f"[Server酱] 发送失败: {result}")
                return False

        except Exception as e:
            logger.error(f"[Server酱] 发送异常: {e}")
            return False

#!/usr/bin/env python3
"""
企业微信机器人通知
"""
import json
import logging
import requests
from typing import List

from .base import BaseNotifier, NotifyMessage, NotifyLevel

logger = logging.getLogger(__name__)


class WeChatNotifier(BaseNotifier):
    """
    企业微信机器人推送

    使用方法:
    1. 在企业微信中创建群聊
    2. 添加机器人，获取 Webhook URL
    3. 配置到 .env: WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.timeout = 10

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    def send(self, message: NotifyMessage) -> bool:
        """发送消息"""
        if not self.webhook_url:
            logger.warning("[微信] Webhook 未配置")
            return False

        try:
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": message.to_markdown()
                }
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )

            result = response.json()

            if result.get("errcode") == 0:
                logger.info(f"[微信] 发送成功: {message.title}")
                return True
            else:
                logger.error(f"[微信] 发送失败: {result}")
                return False

        except Exception as e:
            logger.error(f"[微信] 发送异常: {e}")
            return False

    def send_text(self, content: str, mentioned_list: List[str] = None) -> bool:
        """
        发送纯文本消息

        Args:
            content: 文本内容
            mentioned_list: @ 用户列表 (@all 表示所有人)
        """
        if not self.webhook_url:
            return False

        try:
            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }

            if mentioned_list:
                payload["text"]["mentioned_list"] = mentioned_list

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )

            return response.json().get("errcode") == 0

        except Exception as e:
            logger.error(f"[微信] 发送异常: {e}")
            return False

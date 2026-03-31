#!/usr/bin/env python3
"""
钉钉机器人通知
"""
import logging
import requests

from .base import BaseNotifier, NotifyMessage, NotifyLevel

logger = logging.getLogger(__name__)


class DingTalkNotifier(BaseNotifier):
    """
    钉钉群机器人推送

    使用方法:
    1. 打开钉钉，创建一个群聊
    2. 群设置 → 智能群助手 → 添加机器人
    3. 选择"自定义"机器人
    4. 安全设置选择"自定义关键词"，填入：行情
    5. 复制 Webhook 地址
    6. 配置到 .env: DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.timeout = 10

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    def send(self, message: NotifyMessage) -> bool:
        """发送消息"""
        if not self.webhook_url:
            return False

        try:
            # 钉钉 Markdown 格式
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": message.title,
                    "text": self._format_markdown(message)
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
                logger.info(f"[钉钉] 发送成功: {message.title}")
                return True
            else:
                logger.error(f"[钉钉] 发送失败: {result}")
                return False

        except Exception as e:
            logger.error(f"[钉钉] 发送异常: {e}")
            return False

    def _format_markdown(self, message: NotifyMessage) -> str:
        """转换为钉钉 Markdown 格式"""
        level_emoji = {
            NotifyLevel.INFO: "📢",
            NotifyLevel.WARNING: "⚠️",
            NotifyLevel.ERROR: "❌",
            NotifyLevel.CRITICAL: "🚨"
        }
        emoji = level_emoji.get(message.level, "📢")

        lines = [
            f"## {emoji} {message.title}",
            "",
            f"> 时间: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if message.symbol:
            lines.append(f"> 交易对: {message.symbol}")

        lines.extend([
            "",
            message.content,
            "",
            "---",
            "*行情监控系统自动推送*"  # 包含关键词"行情"
        ])

        return "\n".join(lines)

    def send_text(self, content: str, at_all: bool = False) -> bool:
        """发送纯文本消息"""
        if not self.webhook_url:
            return False

        try:
            payload = {
                "msgtype": "text",
                "text": {"content": content},
                "at": {"isAtAll": at_all}
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )

            return response.json().get("errcode") == 0

        except Exception as e:
            logger.error(f"[钉钉] 发送异常: {e}")
            return False

#!/usr/bin/env python3
"""
Gmail 邮件通知

使用标准库 smtplib 发送 Gmail 邮件
"""
import smtplib
import logging
import ssl
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional

from .base import BaseNotifier, NotifyMessage, NotifyLevel

logger = logging.getLogger(__name__)


class GmailNotifier(BaseNotifier):
    """
    Gmail 邮件通知器

    使用方法:
    1. 开启 Gmail 两步验证
    2. 生成应用专用密码: https://myaccount.google.com/apppasswords
    3. 配置到 .env:
       GMAIL_USER=your_email@gmail.com
       GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx  # 16位应用专用密码，去掉空格
       GMAIL_TO=recipient@example.com
    """

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465

    def __init__(self, user: str, app_password: str, to_addr: str):
        self.user = user
        self.app_password = app_password
        self.to_addr = to_addr

    def is_configured(self) -> bool:
        return bool(self.user and self.app_password and self.to_addr)

    def send(self, message: NotifyMessage) -> bool:
        """发送邮件"""
        if not self.is_configured():
            logger.warning("[Gmail] 配置不完整")
            return False

        try:
            # 构建邮件内容
            level_emoji = {
                NotifyLevel.INFO: "📢",
                NotifyLevel.WARNING: "⚠️",
                NotifyLevel.ERROR: "❌",
                NotifyLevel.CRITICAL: "🚨"
            }
            emoji = level_emoji.get(message.level, "📢")

            body = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{emoji} {message.title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

时间: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"""

            if message.symbol:
                body += f"\n交易对: {message.symbol}"

            body += f"""

{message.content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
此邮件由行情监控系统自动发送"""

            # 创建邮件
            email = MIMEText(body, "plain", "utf-8")
            email["Subject"] = f"[{message.level.value.upper()}] {message.title}"
            email["From"] = self.user
            email["To"] = self.to_addr

            # 发送邮件
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT, context=context) as server:
                server.login(self.user, self.app_password)
                server.sendmail(self.user, self.to_addr, email.as_string())

            logger.info(f"[Gmail] 发送成功: {message.title}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("[Gmail] 认证失败，请检查应用专用密码")
            return False
        except Exception as e:
            logger.error(f"[Gmail] 发送失败: {e}")
            return False

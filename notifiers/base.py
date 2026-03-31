#!/usr/bin/env python3
"""
通知基类

定义通知接口和通用数据结构
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class NotifyLevel(Enum):
    """通知级别"""
    INFO = "info"           # 普通信息
    WARNING = "warning"     # 警告
    ERROR = "error"         # 错误
    CRITICAL = "critical"   # 紧急


@dataclass
class NotifyMessage:
    """通知消息"""
    title: str
    content: str
    level: NotifyLevel = NotifyLevel.INFO
    symbol: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        level_emoji = {
            NotifyLevel.INFO: "📢",
            NotifyLevel.WARNING: "⚠️",
            NotifyLevel.ERROR: "❌",
            NotifyLevel.CRITICAL: "🚨"
        }
        emoji = level_emoji.get(self.level, "📢")

        lines = [
            f"## {emoji} {self.title}",
            "",
            f"> 时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if self.symbol:
            lines.append(f"> 交易对: {self.symbol}")

        lines.extend([
            "",
            self.content,
            "",
            "---",
            "*行情监控系统自动推送*"
        ])

        return "\n".join(lines)


class BaseNotifier(ABC):
    """通知器基类"""

    @abstractmethod
    def send(self, message: NotifyMessage) -> bool:
        """
        发送通知

        Args:
            message: 通知消息

        Returns:
            是否发送成功
        """
        pass

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return True

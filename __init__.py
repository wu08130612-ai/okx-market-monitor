#!/usr/bin/env python3
"""
实时行情监控工具

功能:
- 实时抓取 OKX 持仓信息和委托单
- 委托成交时自动通知
- 持仓跌幅超过 1% 时通知（不含杠杆）
- 实时抓取 OKX 所有加密货币行情
- 检测金叉/死叉信号或高点低点不断抬高的形态
"""
from .core.okx_client import OKXClient
from .core.indicators import Indicators
from .core.pattern_detector import PatternDetector
from .notifiers.manager import NotifierManager, NotifyLevel

__all__ = [
    'OKXClient',
    'Indicators',
    'PatternDetector',
    'NotifierManager',
    'NotifyLevel',
]

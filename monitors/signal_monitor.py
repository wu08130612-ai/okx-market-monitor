#!/usr/bin/env python3
"""
信号监控器

功能：
- 检测金叉死叉信号
- 检测高点低点抬高形态
- 实时抓取所有加密货币行情
"""
import logging
import time
import numpy as np
from typing import Dict, List, Optional, Set
from datetime import datetime

from ..core.okx_client import OKXClient
from ..core.indicators import Indicators
from ..core.pattern_detector import PatternDetector, PatternResult
from ..notifiers.manager import NotifierManager, NotifyLevel
from ..config import (
    EMA_FAST_PERIOD,
    EMA_SLOW_PERIOD,
    PATTERN_LOOKBACK,
    WATCH_SYMBOLS,
    EXCLUDE_SYMBOLS,
    NOTIFY_COOLDOWN
)

# 阈值常量
GAINER_THRESHOLD_PCT = 5.0      # 涨幅榜阈值
LOSER_THRESHOLD_PCT = -5.0      # 跌幅榜阈值
HIGH_VOLUME_THRESHOLD = 10_000_000  # 高成交量阈值

logger = logging.getLogger(__name__)


class SignalMonitor:
    """
    信号监控器

    检测金叉死叉信号和高点低点抬高形态
    """

    def __init__(self, client: OKXClient, notifier: NotifierManager):
        self.client = client
        self.notifier = notifier
        self.pattern_detector = PatternDetector(lookback=PATTERN_LOOKBACK)

        # 已通知的信号（防止重复通知）
        # key: symbol_signal_type, value: 通知时间
        self.notified_signals: Dict[str, datetime] = {}

        # 缓存的 K 线数据
        self.candle_cache: Dict[str, dict] = {}

        # 监控的交易对列表
        self.watch_symbols: List[str] = []
        self._init_watch_symbols()

    def _init_watch_symbols(self):
        """初始化监控的交易对列表"""
        if WATCH_SYMBOLS:
            # 使用用户配置的交易对
            self.watch_symbols = WATCH_SYMBOLS
        else:
            # 获取所有 USDT 永续合约
            instruments = self.client.get_swap_instruments()
            for inst in instruments:
                inst_id = inst.get("instId", "")
                # 过滤 USDT 本位的永续合约
                if inst_id.endswith("-USDT-SWAP"):
                    base = inst_id.replace("-USDT-SWAP", "")
                    # 排除一些特殊交易对
                    if base not in EXCLUDE_SYMBOLS and len(base) <= 10:
                        self.watch_symbols.append(inst_id)

        logger.info(f"[信号监控] 监控 {len(self.watch_symbols)} 个交易对")

    def check_signals(self) -> Dict:
        """
        检查所有交易对的信号

        Returns:
            检查结果
        """
        result = {
            "golden_cross": [],
            "death_cross": [],
            "uptrend": [],
            "downtrend": [],
            "errors": []
        }

        processed = 0
        for symbol in self.watch_symbols:
            try:
                signals = self._check_symbol(symbol)
                if signals:
                    for signal_type, signal_data in signals.items():
                        if signal_type in result:
                            result[signal_type].append(signal_data)
                processed += 1

                # 避免请求过快
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"[信号监控] {symbol} 检查失败: {e}")
                result["errors"].append({"symbol": symbol, "error": str(e)})

        logger.info(f"[信号监控] 检查完成: {processed}/{len(self.watch_symbols)} 个交易对")
        return result

    def _check_symbol(self, symbol: str) -> Optional[Dict]:
        """
        检查单个交易对的信号

        Args:
            symbol: 交易对

        Returns:
            信号数据
        """
        result = {}

        # 获取 K 线数据
        candles = self.client.get_candles(symbol, bar="1H", limit=100)
        if not candles or len(candles) < 50:
            return None

        # 解析 K 线数据
        # OKX K 线格式: [ts, open, high, low, close, vol, ...]
        opens = np.array([float(c[1]) for c in candles])
        highs = np.array([float(c[2]) for c in candles])
        lows = np.array([float(c[3]) for c in candles])
        closes = np.array([float(c[4]) for c in candles])

        current_price = closes[-1]

        # 1. 检测金叉死叉
        cross = Indicators.detect_ema_cross(
            closes,
            fast=EMA_FAST_PERIOD,
            slow=EMA_SLOW_PERIOD
        )

        if cross == "golden_cross":
            signal_key = f"{symbol}_golden_cross"
            if self._should_notify(signal_key):
                result["golden_cross"] = {
                    "symbol": symbol,
                    "price": current_price,
                    "time": datetime.now().isoformat()
                }
                self._send_signal_notification(
                    symbol, "golden_cross", current_price,
                    f"EMA{EMA_FAST_PERIOD} 上穿 EMA{EMA_SLOW_PERIOD}"
                )
                self.notified_signals[signal_key] = datetime.now()

        elif cross == "death_cross":
            signal_key = f"{symbol}_death_cross"
            if self._should_notify(signal_key):
                result["death_cross"] = {
                    "symbol": symbol,
                    "price": current_price,
                    "time": datetime.now().isoformat()
                }
                self._send_signal_notification(
                    symbol, "death_cross", current_price,
                    f"EMA{EMA_FAST_PERIOD} 下穿 EMA{EMA_SLOW_PERIOD}"
                )
                self.notified_signals[signal_key] = datetime.now()

        # 2. 检测形态
        pattern = self.pattern_detector.analyze(highs, lows, closes)

        if pattern.trend == "uptrend" and pattern.strength >= 0.6:
            signal_key = f"{symbol}_uptrend"
            if self._should_notify(signal_key):
                details = []
                if pattern.higher_highs:
                    details.append("高点抬高")
                if pattern.higher_lows:
                    details.append("低点抬高")

                result["uptrend"] = {
                    "symbol": symbol,
                    "price": current_price,
                    "strength": pattern.strength,
                    "time": datetime.now().isoformat()
                }
                self._send_signal_notification(
                    symbol, "uptrend", current_price,
                    f"上升趋势: {', '.join(details)}"
                )
                self.notified_signals[signal_key] = datetime.now()

        elif pattern.trend == "downtrend" and pattern.strength >= 0.6:
            signal_key = f"{symbol}_downtrend"
            if self._should_notify(signal_key):
                result["downtrend"] = {
                    "symbol": symbol,
                    "price": current_price,
                    "strength": pattern.strength,
                    "time": datetime.now().isoformat()
                }
                self.notified_signals[signal_key] = datetime.now()
                # 下降趋势不发通知，只记录

        return result if result else None

    def _should_notify(self, signal_key: str) -> bool:
        """
        检查是否应该通知

        Args:
            signal_key: 信号键

        Returns:
            是否应该通知
        """
        if signal_key not in self.notified_signals:
            return True

        last_time = self.notified_signals[signal_key]
        elapsed = (datetime.now() - last_time).total_seconds()

        # 冷却时间检查
        return elapsed >= NOTIFY_COOLDOWN

    def _send_signal_notification(
        self,
        symbol: str,
        signal_type: str,
        price: float,
        details: str
    ):
        """
        发送信号通知

        Args:
            symbol: 交易对
            signal_type: 信号类型
            price: 当前价格
            details: 详细信息
        """
        self.notifier.notify_signal(symbol, signal_type, price, details)

    def get_tickers_summary(self) -> Dict:
        """
        获取所有交易对行情摘要

        Returns:
            行情摘要
        """
        tickers = self.client.get_swap_tickers()

        summary = {
            "total": len(tickers),
            "gainers": [],  # 涨幅榜
            "losers": [],   # 跌幅榜
            "high_volume": []  # 高成交量
        }

        for ticker in tickers:
            symbol = ticker.get("instId", "")
            if symbol not in self.watch_symbols:
                continue

            change_24h = float(ticker.get("changeUtc24h", 0))
            vol_24h = float(ticker.get("vol24h", 0))
            last_price = float(ticker.get("last", 0))

            data = {
                "symbol": symbol,
                "price": last_price,
                "change_24h": change_24h,
                "volume": vol_24h
            }

            # 涨幅榜
            if change_24h > GAINER_THRESHOLD_PCT:
                summary["gainers"].append(data)

            # 跌幅榜
            if change_24h < LOSER_THRESHOLD_PCT:
                summary["losers"].append(data)

            # 高成交量
            if vol_24h > HIGH_VOLUME_THRESHOLD:
                summary["high_volume"].append(data)

        # 排序
        summary["gainers"].sort(key=lambda x: x["change_24h"], reverse=True)
        summary["losers"].sort(key=lambda x: x["change_24h"])
        summary["high_volume"].sort(key=lambda x: x["volume"], reverse=True)

        # 取前 10
        summary["gainers"] = summary["gainers"][:10]
        summary["losers"] = summary["losers"][:10]
        summary["high_volume"] = summary["high_volume"][:10]

        return summary

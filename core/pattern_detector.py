#!/usr/bin/env python3
"""
形态识别器

检测:
- 高点低点不断抬高（上升趋势）
- 高点低点不断降低（下降趋势）
- 趋势结构分析
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .indicators import Indicators


@dataclass
class PatternResult:
    """形态识别结果"""
    trend: str           # "uptrend" / "downtrend" / "sideways"
    higher_highs: bool   # 高点抬高
    higher_lows: bool    # 低点抬高
    lower_highs: bool    # 高点降低
    lower_lows: bool     # 低点降低
    strength: float      # 趋势强度 (0-1)
    signal: str          # "buy" / "sell" / "hold"


class PatternDetector:
    """
    形态识别器

    识别趋势形态和关键结构
    """

    def __init__(self, lookback: int = 20):
        """
        初始化

        Args:
            lookback: 回溯周期
        """
        self.lookback = lookback

    def find_local_extremes(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        window: int = 3
    ) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
        """
        寻找局部高点和低点

        Args:
            highs: 最高价数组
            lows: 最低价数组
            window: 确认窗口（前后各多少根 K 线）

        Returns:
            (局部高点列表, 局部低点列表)
            每个元素为 (索引, 价格)
        """
        local_highs = []
        local_lows = []

        for i in range(window, len(highs) - window):
            # 局部高点：中间 K 线高点最高
            is_high = True
            for j in range(-window, window + 1):
                if j != 0 and highs[i] <= highs[i + j]:
                    is_high = False
                    break
            if is_high:
                local_highs.append((i, highs[i]))

            # 局部低点：中间 K 线低点最低
            is_low = True
            for j in range(-window, window + 1):
                if j != 0 and lows[i] >= lows[i + j]:
                    is_low = False
                    break
            if is_low:
                local_lows.append((i, lows[i]))

        return local_highs, local_lows

    def analyze(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> PatternResult:
        """
        分析形态

        Args:
            highs: 最高价数组
            lows: 最低价数组
            closes: 收盘价数组

        Returns:
            PatternResult
        """
        if len(highs) < self.lookback:
            return PatternResult(
                trend="sideways",
                higher_highs=False,
                higher_lows=False,
                lower_highs=False,
                lower_lows=False,
                strength=0.0,
                signal="hold"
            )

        # 寻找局部极值点
        local_highs, local_lows = self.find_local_extremes(
            highs[-self.lookback:],
            lows[-self.lookback:],
            window=3
        )

        # 检查高点是否抬高
        higher_highs = self._check_ascending(local_highs)
        # 检查低点是否抬高
        higher_lows = self._check_ascending(local_lows)
        # 检查高点是否降低
        lower_highs = self._check_descending(local_highs)
        # 检查低点是否降低
        lower_lows = self._check_descending(local_lows)

        # 判断趋势
        trend = "sideways"
        strength = 0.0
        signal = "hold"

        if higher_highs and higher_lows:
            # 强上升趋势
            trend = "uptrend"
            strength = 0.9
            signal = "buy"
        elif higher_lows:
            # 弱上升趋势（低点抬高）
            trend = "uptrend"
            strength = 0.6
            signal = "buy"
        elif lower_highs and lower_lows:
            # 强下降趋势
            trend = "downtrend"
            strength = 0.9
            signal = "sell"
        elif lower_highs:
            # 弱下降趋势（高点降低）
            trend = "downtrend"
            strength = 0.6
            signal = "sell"

        return PatternResult(
            trend=trend,
            higher_highs=higher_highs,
            higher_lows=higher_lows,
            lower_highs=lower_highs,
            lower_lows=lower_lows,
            strength=strength,
            signal=signal
        )

    def _check_ascending(self, extremes: List[Tuple[int, float]], min_count: int = 3) -> bool:
        """
        检查极值点是否递增

        Args:
            extremes: 极值点列表
            min_count: 最少需要的极值点数量

        Returns:
            是否递增
        """
        if len(extremes) < min_count:
            return False

        # 取最近的极值点
        recent = [e[1] for e in extremes[-min_count:]]

        # 检查是否递增
        for i in range(len(recent) - 1):
            if recent[i] >= recent[i + 1]:
                return False

        return True

    def _check_descending(self, extremes: List[Tuple[int, float]], min_count: int = 3) -> bool:
        """
        检查极值点是否递减

        Args:
            extremes: 极值点列表
            min_count: 最少需要的极值点数量

        Returns:
            是否递减
        """
        if len(extremes) < min_count:
            return False

        # 取最近的极值点
        recent = [e[1] for e in extremes[-min_count:]]

        # 检查是否递减
        for i in range(len(recent) - 1):
            if recent[i] <= recent[i + 1]:
                return False

        return True

    def detect_breakout(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        lookback: int = 20
    ) -> Dict:
        """
        检测突破

        Args:
            highs: 最高价数组
            lows: 最低价数组
            closes: 收盘价数组
            lookback: 回溯周期

        Returns:
            突破信息
        """
        if len(closes) < lookback:
            return {"breakout": None, "direction": None}

        recent_high = np.max(highs[-lookback:-1])
        recent_low = np.min(lows[-lookback:-1])
        current_close = closes[-1]

        if current_close > recent_high:
            return {"breakout": "up", "level": recent_high, "strength": 0.8}
        elif current_close < recent_low:
            return {"breakout": "down", "level": recent_low, "strength": 0.8}

        return {"breakout": None, "direction": None}


# 测试代码
if __name__ == "__main__":
    import numpy as np

    print("=" * 50)
    print("形态识别测试")
    print("=" * 50)

    # 生成上升趋势数据
    np.random.seed(42)
    base = 100
    trend = np.linspace(0, 10, 50)
    noise = np.random.randn(50) * 1.5
    closes = base + trend + np.cumsum(noise * 0.1)
    highs = closes + np.abs(np.random.randn(50)) * 2
    lows = closes - np.abs(np.random.randn(50)) * 2

    detector = PatternDetector(lookback=30)
    result = detector.analyze(highs, lows, closes)

    print(f"\n趋势: {result.trend}")
    print(f"高点抬高: {result.higher_highs}")
    print(f"低点抬高: {result.higher_lows}")
    print(f"趋势强度: {result.strength:.2f}")
    print(f"信号: {result.signal}")

    print("\n测试完成!")

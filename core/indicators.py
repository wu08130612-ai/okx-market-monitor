#!/usr/bin/env python3
"""
技术指标计算

提供:
- EMA 指数移动平均线
- RSI 相对强弱指标
- MACD 指标
- 金叉死叉检测
"""
import numpy as np
from typing import Tuple, Optional


class Indicators:
    """技术指标计算器"""

    @staticmethod
    def ema(closes: np.ndarray, period: int) -> np.ndarray:
        """
        计算 EMA (指数移动平均线)

        Args:
            closes: 收盘价数组
            period: 周期

        Returns:
            EMA 数组
        """
        if len(closes) < period:
            return np.array([])

        closes = np.asarray(closes, dtype=float)
        multiplier = 2.0 / (period + 1)

        # 初始 SMA
        ema = np.zeros(len(closes))
        ema[period - 1] = np.mean(closes[:period])

        # 递归计算 EMA
        for i in range(period, len(closes)):
            ema[i] = (closes[i] - ema[i - 1]) * multiplier + ema[i - 1]

        return ema[period - 1:]

    @staticmethod
    def ema_value(closes: np.ndarray, period: int) -> float:
        """获取最新 EMA 值"""
        ema = Indicators.ema(closes, period)
        return ema[-1] if len(ema) > 0 else 0.0

    @staticmethod
    def rsi(closes: np.ndarray, period: int = 14) -> float:
        """
        计算 RSI (相对强弱指标)

        Args:
            closes: 收盘价数组
            period: 周期

        Returns:
            RSI 值 (0-100)
        """
        if len(closes) < period + 1:
            return 50.0

        closes = np.asarray(closes, dtype=float)
        deltas = np.diff(closes)

        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        if avg_loss == 0:
            return 100.0

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def macd(
        closes: np.ndarray,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[float, float, float]:
        """
        计算 MACD

        Args:
            closes: 收盘价数组
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            (dif, dea, macd_histogram)
        """
        if len(closes) < slow + signal:
            return 0.0, 0.0, 0.0

        ema_fast = Indicators.ema(closes, fast)
        ema_slow = Indicators.ema(closes, slow)

        # 对齐长度
        min_len = min(len(ema_fast), len(ema_slow))
        if min_len == 0:
            return 0.0, 0.0, 0.0

        ema_fast = ema_fast[-min_len:]
        ema_slow = ema_slow[-min_len:]

        # DIF = 快线 - 慢线
        dif = ema_fast - ema_slow

        # DEA = DIF 的 EMA
        dea = Indicators.ema(dif, signal)
        if len(dea) == 0:
            return dif[-1], 0.0, 0.0

        # MACD 柱 = (DIF - DEA) * 2
        macd_hist = (dif[-1] - dea[-1]) * 2

        return dif[-1], dea[-1], macd_hist

    @staticmethod
    def detect_ema_cross(
        closes: np.ndarray,
        fast: int = 12,
        slow: int = 26
    ) -> str:
        """
        检测 EMA 金叉死叉

        Args:
            closes: 收盘价数组
            fast: 快线周期
            slow: 慢线周期

        Returns:
            "golden_cross": 金叉（快线上穿慢线）
            "death_cross": 死叉（快线下穿慢线）
            "none": 无交叉
        """
        if len(closes) < slow + 2:
            return "none"

        # 计算 EMA 序列
        ema_fast = Indicators.ema(closes, fast)
        ema_slow = Indicators.ema(closes, slow)

        if len(ema_fast) < 2 or len(ema_slow) < 2:
            return "none"

        # 对齐长度
        min_len = min(len(ema_fast), len(ema_slow))
        ema_fast = ema_fast[-min_len:]
        ema_slow = ema_slow[-min_len:]

        # 当前和前一根 K 线的差值
        current_diff = ema_fast[-1] - ema_slow[-1]
        prev_diff = ema_fast[-2] - ema_slow[-2]

        # 金叉：快线从下方穿越慢线
        if prev_diff < 0 and current_diff > 0:
            return "golden_cross"

        # 死叉：快线从上方穿越慢线
        if prev_diff > 0 and current_diff < 0:
            return "death_cross"

        return "none"

    @staticmethod
    def atr(
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int = 14
    ) -> float:
        """
        计算 ATR (平均真实波幅)

        Args:
            highs: 最高价数组
            lows: 最低价数组
            closes: 收盘价数组
            period: 周期

        Returns:
            ATR 值
        """
        if len(closes) < period + 1:
            return 0.0

        highs = np.asarray(highs, dtype=float)
        lows = np.asarray(lows, dtype=float)
        closes = np.asarray(closes, dtype=float)

        # 真实波幅
        tr1 = highs - lows
        tr2 = np.abs(highs - np.roll(closes, 1))
        tr3 = np.abs(lows - np.roll(closes, 1))

        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        tr[0] = tr1[0]  # 第一根没有前值

        # 平均真实波幅
        atr = np.mean(tr[-period:])
        return atr


def ema_series(closes: np.ndarray, period: int) -> np.ndarray:
    """EMA 序列计算的便捷函数"""
    return Indicators.ema(closes, period)


# 测试代码
if __name__ == "__main__":
    import numpy as np

    # 生成测试数据
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(50) * 2)

    print("=" * 50)
    print("技术指标测试")
    print("=" * 50)

    # EMA
    ema20 = Indicators.ema_value(closes, 20)
    print(f"\nEMA(20): {ema20:.2f}")

    # RSI
    rsi = Indicators.rsi(closes, 14)
    print(f"RSI(14): {rsi:.2f}")

    # MACD
    dif, dea, macd_hist = Indicators.macd(closes)
    print(f"MACD: DIF={dif:.4f}, DEA={dea:.4f}, Histogram={macd_hist:.4f}")

    # 交叉检测
    cross = Indicators.detect_ema_cross(closes)
    print(f"EMA 交叉: {cross}")

    print("\n测试完成!")

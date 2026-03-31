#!/usr/bin/env python3
"""
持仓监控器

功能：监控持仓跌幅（不含杠杆），超过阈值时发送通知
"""
import logging
import time
from typing import Dict, Optional
from datetime import datetime

from ..core.okx_client import OKXClient
from ..notifiers.manager import NotifierManager, NotifyLevel
from ..config import POSITION_LOSS_THRESHOLD, NOTIFY_COOLDOWN

logger = logging.getLogger(__name__)


class PositionMonitor:
    """
    持仓监控器

    监控持仓跌幅（不含杠杆），超过阈值时发送通知
    """

    def __init__(self, client: OKXClient, notifier: NotifierManager):
        self.client = client
        self.notifier = notifier

        # 已通知的持仓，防止重复通知
        # key: symbol_direction, value: (通知时间, 跌幅)
        self.notified_positions: Dict[str, tuple] = {}

    def check_positions(self) -> Dict:
        """
        检查所有持仓

        Returns:
            检查结果
        """
        result = {
            "positions": [],
            "alerts": []
        }

        # 获取合约持仓
        positions = self.client.get_positions(instType="SWAP")

        if not positions:
            logger.debug("[持仓监控] 无持仓")
            return result

        for pos in positions:
            alert = self._check_single_position(pos)
            if alert:
                result["positions"].append(pos)
                result["alerts"].append(alert)

        return result

    def _check_single_position(self, pos: Dict) -> Optional[Dict]:
        """
        检查单个持仓

        Args:
            pos: 持仓数据

        Returns:
            告警信息（如果有）
        """
        inst_id = pos.get("instId", "")
        pos_side = pos.get("posSide", "net")
        avg_px = float(pos.get("avgPx", 0))  # 开仓均价
        pos_qty = float(pos.get("pos", 0))

        if pos_qty == 0 or avg_px == 0:
            return None

        # 获取当前价格
        ticker = self.client.get_ticker(inst_id)
        if not ticker:
            logger.warning(f"[持仓监控] 无法获取 {inst_id} 行情")
            return None

        current_price = float(ticker.get("last", 0))
        if current_price == 0:
            return None

        # 计算跌幅（不含杠杆）
        # 跌幅 = (开仓价 - 当前价) / 开仓价
        # 注意：这是价格跌幅，不是账户亏损比例
        is_long = pos_side == "long" or (pos_side == "net" and pos_qty > 0)

        if is_long:
            # 多仓：价格下跌时亏损
            loss_pct = (avg_px - current_price) / avg_px if avg_px > 0 else 0
        else:
            # 空仓：价格上涨时亏损
            loss_pct = (current_price - avg_px) / avg_px if avg_px > 0 else 0

        # 检查是否超过阈值
        threshold = POSITION_LOSS_THRESHOLD

        if loss_pct >= threshold:
            notify_key = f"{inst_id}_{pos_side}"

            # 检查是否需要通知（冷却时间检查）
            if not self._should_notify(notify_key, loss_pct):
                return None

            # 发送通知
            direction = "多仓" if is_long else "空仓"
            self.notifier.notify_position_loss(
                symbol=inst_id,
                direction=direction,
                open_price=avg_px,
                current_price=current_price,
                loss_pct=loss_pct,
                threshold=threshold
            )

            # 记录已通知
            self.notified_positions[notify_key] = (datetime.now(), loss_pct)

            logger.warning(
                f"[持仓监控] {inst_id} {direction}跌幅 {loss_pct*100:.2f}% 已通知"
            )

            return {
                "symbol": inst_id,
                "direction": direction,
                "open_price": avg_px,
                "current_price": current_price,
                "loss_pct": loss_pct,
                "threshold": threshold
            }
        else:
            # 跌幅恢复，清除通知记录
            notify_key = f"{inst_id}_{pos_side}"
            if notify_key in self.notified_positions:
                del self.notified_positions[notify_key]

        return None

    def _should_notify(self, key: str, loss_pct: float) -> bool:
        """
        检查是否应该通知

        Args:
            key: 通知键
            loss_pct: 跌幅

        Returns:
            是否应该通知
        """
        if key not in self.notified_positions:
            return True

        last_time, last_loss_pct = self.notified_positions[key]

        # 检查冷却时间
        elapsed = (datetime.now() - last_time).total_seconds()
        if elapsed < NOTIFY_COOLDOWN:
            # 冷却期内，只有跌幅增加超过 0.5% 才再次通知
            if loss_pct - last_loss_pct < 0.005:
                return False

        return True

    def get_position_summary(self) -> Dict:
        """
        获取持仓摘要

        Returns:
            持仓摘要
        """
        positions = self.client.get_positions(instType="SWAP")

        summary = {
            "total_count": 0,
            "long_count": 0,
            "short_count": 0,
            "total_value": 0.0,
            "positions": []
        }

        for pos in positions:
            pos_qty = float(pos.get("pos", 0))
            if pos_qty == 0:
                continue

            summary["total_count"] += 1
            pos_side = pos.get("posSide", "net")

            if pos_side == "long" or (pos_side == "net" and pos_qty > 0):
                summary["long_count"] += 1
            else:
                summary["short_count"] += 1

            # 获取当前价格计算价值
            inst_id = pos.get("instId", "")
            ticker = self.client.get_ticker(inst_id)
            if ticker:
                current_price = float(ticker.get("last", 0))
                pos_value = abs(pos_qty) * current_price
                summary["total_value"] += pos_value

            summary["positions"].append({
                "symbol": inst_id,
                "side": pos_side,
                "qty": pos_qty,
                "avgPx": pos.get("avgPx", 0)
            })

        return summary

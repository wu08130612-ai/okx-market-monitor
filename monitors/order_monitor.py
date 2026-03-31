#!/usr/bin/env python3
"""
委托单监控器

功能：监控未成交订单，检测成交状态并发送通知
"""
import logging
from typing import Dict, List, Set
from datetime import datetime

from ..core.okx_client import OKXClient
from ..notifiers.manager import NotifierManager
from ..config import ORDER_CHECK_INTERVAL

logger = logging.getLogger(__name__)


class OrderMonitor:
    """
    委托单监控器

    监控未成交订单，检测成交状态并发送通知
    """

    def __init__(self, client: OKXClient, notifier: NotifierManager):
        self.client = client
        self.notifier = notifier

        # 已记录的订单 ID
        self.known_orders: Set[str] = set()
        # 已通知的成交订单
        self.notified_fills: Set[str] = set()

    def check_orders(self) -> Dict:
        """
        检查所有委托单

        Returns:
            检查结果
        """
        result = {
            "pending_orders": [],
            "filled_orders": [],
            "alerts": []
        }

        # 获取未成交订单（合约）
        swap_orders = self.client.get_orders_pending(instType="SWAP")
        result["pending_orders"].extend(swap_orders)

        # 获取未成交订单（现货）
        spot_orders = self.client.get_orders_pending(instType="SPOT")
        result["pending_orders"].extend(spot_orders)

        # 获取策略委托订单
        algo_orders = self.client.get_algo_orders(instType="SWAP")
        result["pending_orders"].extend(algo_orders)

        # 更新已知订单集合
        current_order_ids = set()
        for order in swap_orders + spot_orders:
            order_id = order.get("ordId", "")
            if order_id:
                current_order_ids.add(order_id)

        # 检测新成交的订单
        filled = self._detect_filled_orders(current_order_ids)
        result["filled_orders"] = filled

        # 发送通知
        for fill in filled:
            self._notify_fill(fill)
            result["alerts"].append({
                "type": "order_filled",
                "order_id": fill.get("ordId", ""),
                "symbol": fill.get("instId", "")
            })

        # 更新已知订单
        self.known_orders = current_order_ids

        return result

    def _detect_filled_orders(self, current_order_ids: Set[str]) -> List[Dict]:
        """
        检测已成交的订单

        Args:
            current_order_ids: 当前未成交订单 ID 集合

        Returns:
            已成交订单列表
        """
        filled = []

        # 找出之前存在但现在不存在的订单
        disappeared = self.known_orders - current_order_ids

        for order_id in disappeared:
            # 尝试从历史订单中获取成交信息
            # 由于我们没有保存原始订单信息，这里只能记录 ID
            if order_id not in self.notified_fills:
                filled.append({
                    "ordId": order_id,
                    "status": "filled",
                    "instId": "未知",  # 需要改进
                    "fillPx": "未知",
                    "fillSz": "未知"
                })
                self.notified_fills.add(order_id)

        return filled

    def _notify_fill(self, fill: Dict):
        """
        发送成交通知

        Args:
            fill: 成交信息
        """
        order_id = fill.get("ordId", "")
        symbol = fill.get("instId", "未知")

        logger.info(f"[委托监控] 订单成交: {symbol} {order_id}")

        # 由于信息不完整，发送简化通知
        self.notifier.notify(
            title=f"✅ 订单成交: {symbol}",
            content=f"""**订单已成交**

- **订单ID**: {order_id}
- **交易对**: {symbol}

> 请确认订单详情。""",
            level="info",
            symbol=symbol
        )

    def get_order_summary(self) -> Dict:
        """
        获取订单摘要

        Returns:
            订单摘要
        """
        swap_orders = self.client.get_orders_pending(instType="SWAP")
        spot_orders = self.client.get_orders_pending(instType="SPOT")
        algo_orders = self.client.get_algo_orders(instType="SWAP")

        return {
            "swap_pending": len(swap_orders),
            "spot_pending": len(spot_orders),
            "algo_pending": len(algo_orders),
            "total_pending": len(swap_orders) + len(spot_orders) + len(algo_orders)
        }

    def init_orders(self):
        """初始化已知订单集合（首次启动时调用）"""
        swap_orders = self.client.get_orders_pending(instType="SWAP")
        spot_orders = self.client.get_orders_pending(instType="SPOT")

        for order in swap_orders + spot_orders:
            order_id = order.get("ordId", "")
            if order_id:
                self.known_orders.add(order_id)

        logger.info(f"[委托监控] 初始化: 已记录 {len(self.known_orders)} 个未成交订单")

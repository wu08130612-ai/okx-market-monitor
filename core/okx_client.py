#!/usr/bin/env python3
"""
OKX API 客户端

直接使用 REST API 访问 OKX 交易所
"""
import hmac
import base64
import hashlib
import json
import logging
import time
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OKXClient:
    """
    OKX REST API 客户端

    支持公共和私有 API 调用
    """

    BASE_URL = "https://www.okx.com"

    def __init__(
        self,
        api_key: str = "",
        secret: str = "",
        passphrase: str = "",
        demo: bool = False
    ):
        """
        初始化客户端

        Args:
            api_key: API Key
            secret: Secret Key
            passphrase: API Passphrase
            demo: 是否使用模拟交易
        """
        self.api_key = api_key
        self.secret = secret
        self.passphrase = passphrase
        self.demo = demo

        # 请求超时
        self.timeout = 30

        # 模拟交易需要特殊 header
        self.headers = {
            "Content-Type": "application/json"
        }
        if demo:
            self.headers["x-simulated-trading"] = "1"

    def _sign(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """
        生成签名

        Args:
            timestamp: 时间戳
            method: HTTP 方法
            path: 请求路径
            body: 请求体

        Returns:
            签名字符串
        """
        message = f"{timestamp}{method}{path}{body}"
        mac = hmac.new(
            self.secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode("utf-8")

    def _get_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """获取请求头"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        sign = self._sign(timestamp, method, path, body)

        headers = self.headers.copy()
        headers.update({
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
        })
        return headers

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None
    ) -> Dict:
        """
        发送请求

        Args:
            method: HTTP 方法
            path: 请求路径
            params: URL 参数
            body: 请求体

        Returns:
            响应数据
        """
        url = f"{self.BASE_URL}{path}"

        # 构建查询字符串
        query_string = ""
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            if query_string:
                url += f"?{query_string}"

        # 请求体
        body_str = json.dumps(body) if body else ""

        # 获取请求头
        request_path = path
        if query_string:
            request_path += f"?{query_string}"
        headers = self._get_headers(method, request_path, body_str)

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=body_str, timeout=self.timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, data=body_str, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            result = response.json()

            if result.get("code") != "0":
                error_msg = result.get("msg", result.get("data", "Unknown error"))
                logger.error(f"[OKX] API 错误: {error_msg}")
                return {"ok": False, "error": error_msg}

            return {"ok": True, "data": result.get("data", [])}

        except requests.exceptions.Timeout:
            logger.error(f"[OKX] 请求超时: {path}")
            return {"ok": False, "error": "请求超时"}
        except Exception as e:
            logger.error(f"[OKX] 请求异常: {e}")
            return {"ok": False, "error": str(e)}

    # ==================== 公共 API ====================

    def get_instruments(self, instType: str = "SPOT") -> List[Dict]:
        """
        获取交易对列表

        Args:
            instType: 工具类型 (SPOT, SWAP, FUTURES)

        Returns:
            交易对列表
        """
        result = self.request("GET", "/api/v5/public/instruments", {"instType": instType})
        if result.get("ok"):
            return result.get("data", [])
        return []

    def get_ticker(self, instId: str) -> Optional[Dict]:
        """
        获取行情

        Args:
            instId: 交易对

        Returns:
            行情数据
        """
        result = self.request("GET", "/api/v5/market/ticker", {"instId": instId})
        if result.get("ok"):
            data = result.get("data", [])
            return data[0] if data else None
        return None

    def get_candles(
        self,
        instId: str,
        bar: str = "1H",
        limit: int = 100
    ) -> List[List]:
        """
        获取 K 线数据

        Args:
            instId: 交易对
            bar: 时间周期 (1m, 5m, 15m, 1H, 4H, 1D)
            limit: 数量限制

        Returns:
            K 线数据 [[ts, open, high, low, close, vol, volCcy, volCcyQuote, confirm], ...]
        """
        result = self.request("GET", "/api/v5/market/candles", {
            "instId": instId,
            "bar": bar,
            "limit": str(limit)
        })
        if result.get("ok"):
            data = result.get("data", [])
            # OKX 返回降序（最新在前），反转为升序
            return list(reversed(data))
        return []

    # ==================== 账户 API ====================

    def get_balance(self) -> List[Dict]:
        """获取账户余额"""
        result = self.request("GET", "/api/v5/account/balance")
        if result.get("ok"):
            data = result.get("data", [])
            if data:
                return data[0].get("details", [])
        return []

    def get_positions(self, instType: Optional[str] = None) -> List[Dict]:
        """
        获取持仓

        Args:
            instType: 工具类型 (SPOT, MARGIN, SWAP)

        Returns:
            持仓列表
        """
        params = {}
        if instType:
            params["instType"] = instType
        result = self.request("GET", "/api/v5/account/positions", params)
        if result.get("ok"):
            return result.get("data", [])
        return []

    # ==================== 订单 API ====================

    def get_orders_pending(self, instType: str = "SPOT", limit: int = 100) -> List[Dict]:
        """
        获取未成交订单

        Args:
            instType: 工具类型
            limit: 数量限制

        Returns:
            订单列表
        """
        result = self.request("GET", "/api/v5/trade/orders-pending", {
            "instType": instType,
            "limit": str(limit)
        })
        if result.get("ok"):
            return result.get("data", [])
        return []

    def get_algo_orders(self, instType: str = "SWAP", status: str = "live") -> List[Dict]:
        """
        获取策略委托订单

        Args:
            instType: 工具类型
            status: 状态 (live, pending)

        Returns:
            订单列表
        """
        result = self.request("GET", "/api/v5/trade/orders-algo-pending", {
            "instType": instType,
            "algoClOrdId": "",
            "algoId": "",
            "orderType": "conditional"
        })
        if result.get("ok"):
            return result.get("data", [])
        return []

    def get_order_history(self, instId: str, limit: int = 100) -> List[Dict]:
        """
        获取历史订单

        Args:
            instId: 交易对
            limit: 数量限制

        Returns:
            订单列表
        """
        result = self.request("GET", "/api/v5/trade/orders-history", {
            "instId": instId,
            "limit": str(limit)
        })
        if result.get("ok"):
            return result.get("data", [])
        return []

    # ==================== 便捷方法 ====================

    def get_swap_tickers(self) -> List[Dict]:
        """获取所有永续合约行情"""
        result = self.request("GET", "/api/v5/market/tickers", {"instType": "SWAP"})
        if result.get("ok"):
            return result.get("data", [])
        return []

    def get_swap_instruments(self) -> List[Dict]:
        """获取所有永续合约交易对"""
        return self.get_instruments("SWAP")


# 测试代码
if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("OKX Client 测试")
    print("=" * 50)

    client = OKXClient()

    # 测试公共 API
    print("\n[测试] 获取 BTC-USDT 行情...")
    ticker = client.get_ticker("BTC-USDT-SWAP")
    if ticker:
        print(f"最新价: {ticker.get('last')}")
        print(f"24h 涨跌: {ticker.get('changeUtc24h')}%")

    print("\n[测试] 获取 ETH-USDT K 线...")
    candles = client.get_candles("ETH-USDT-SWAP", "1H", 5)
    for c in candles[-3:]:
        print(f"  时间: {c[0]}, 开: {c[1]}, 高: {c[2]}, 低: {c[3]}, 收: {c[4]}")

    print("\n测试完成!")

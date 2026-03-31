#!/usr/bin/env python3
"""
通知管理器

统一管理多个推送渠道
"""
import logging
from typing import Dict, Optional

from .base import NotifyLevel, NotifyMessage
from .wechat import WeChatNotifier
from .serverchan import ServerChanNotifier
from .qmsg import QmsgNotifier
from .gmail import GmailNotifier
from .dingtalk import DingTalkNotifier

logger = logging.getLogger(__name__)


class NotifierManager:
    """
    通知管理器 - 统一管理多个推送渠道
    """

    def __init__(self):
        self.notifiers = []
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        import os

        # 钉钉机器人
        dingtalk_webhook = os.getenv("DINGTALK_WEBHOOK")
        if dingtalk_webhook:
            self.notifiers.append(DingTalkNotifier(dingtalk_webhook))
            logger.info("[推送] 已加载钉钉机器人")

        # 企业微信
        wechat_webhook = os.getenv("WECHAT_WEBHOOK")
        if wechat_webhook:
            self.notifiers.append(WeChatNotifier(wechat_webhook))
            logger.info("[推送] 已加载企业微信机器人")

        # Server酱
        serverchan_key = os.getenv("SERVERCHAN_KEY")
        if serverchan_key:
            self.notifiers.append(ServerChanNotifier(serverchan_key))
            logger.info("[推送] 已加载 Server酱")

        # Qmsg酱
        qmsg_key = os.getenv("QMSG_KEY")
        qmsg_qq = os.getenv("QMSG_QQ", "")
        if qmsg_key:
            self.notifiers.append(QmsgNotifier(qmsg_key, qmsg_qq))
            logger.info("[推送] 已加载 Qmsg酱")

        # Gmail
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        gmail_to = os.getenv("GMAIL_TO")
        if gmail_user and gmail_password and gmail_to:
            self.notifiers.append(GmailNotifier(gmail_user, gmail_password, gmail_to))
            logger.info("[推送] 已加载 Gmail")

    def notify(
        self,
        title: str,
        content: str,
        level: NotifyLevel = NotifyLevel.INFO,
        symbol: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        发送通知到所有已配置的渠道

        Args:
            title: 标题
            content: 内容
            level: 级别
            symbol: 交易对（可选）

        Returns:
            各渠道发送结果
        """
        """
        发送通知到所有已配置的渠道

        Args:
            title: 标题
            content: 内容
            level: 级别
            symbol: 交易对

        Returns:
            各渠道发送结果
        """
        if not self.notifiers:
            logger.warning("未配置任何推送渠道")
            return {}

        message = NotifyMessage(
            title=title,
            content=content,
            level=level,
            symbol=symbol
        )

        results = {}
        for notifier in self.notifiers:
            name = notifier.__class__.__name__
            if notifier.is_configured():
                results[name] = notifier.send(message)
            else:
                results[name] = False

        return results

    def notify_position_loss(
        self,
        symbol: str,
        direction: str,
        open_price: float,
        current_price: float,
        loss_pct: float,
        threshold: float
    ):
        """
        发送持仓跌幅通知

        Args:
            symbol: 交易对
            direction: 方向
            open_price: 开仓价
            current_price: 当前价
            loss_pct: 跌幅
            threshold: 阈值
        """
        title = f"⚠️ 持仓跌幅告警: {symbol}"

        content = f"""**{direction}跌幅超过阈值**

- **交易对**: {symbol}
- **方向**: {direction}
- **开仓价**: ${open_price:,.4f}
- **当前价**: ${current_price:,.4f}
- **跌幅**: {loss_pct * 100:.2f}%
- **阈值**: {threshold * 100:.1f}%

> 请及时关注市场变化，考虑调整仓位或止损。"""

        self.notify(title, content, NotifyLevel.WARNING, symbol)

    def notify_order_filled(
        self,
        symbol: str,
        side: str,
        price: float,
        amount: float,
        order_type: str = "market"
    ):
        """
        发送订单成交通知

        Args:
            symbol: 交易对
            side: 方向 (buy/sell)
            price: 成交价
            amount: 成交量
            order_type: 订单类型
        """
        emoji = "🟢" if side == "buy" else "🔴"
        title = f"{emoji} 订单成交: {symbol}"

        content = f"""**订单已成交**

- **交易对**: {symbol}
- **方向**: {"买入" if side == "buy" else "卖出"}
- **价格**: ${price:,.4f}
- **数量**: {amount}
- **金额**: ${price * amount:,.2f}
- **订单类型**: {order_type}"""

        self.notify(title, content, NotifyLevel.INFO, symbol)

    def notify_signal(
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
            signal_type: 信号类型 (golden_cross/death_cross/uptrend)
            price: 当前价格
            details: 详细信息
        """
        signal_names = {
            "golden_cross": "🟢 金叉信号",
            "death_cross": "🔴 死叉信号",
            "uptrend": "📈 上升趋势",
            "downtrend": "📉 下降趋势"
        }

        signal_name = signal_names.get(signal_type, signal_type)
        title = f"{signal_name}: {symbol}"

        content = f"""**检测到交易信号**

- **交易对**: {symbol}
- **信号类型**: {signal_name}
- **当前价格**: ${price:,.4f}
- **详情**: {details}

> 请结合其他指标判断是否入场。"""

        level = NotifyLevel.WARNING if signal_type == "death_cross" else NotifyLevel.INFO
        self.notify(title, content, level, symbol)

    def notify_critical(self, title: str, message: str):
        """发送紧急告警"""
        self.notify(f"🚨 {title}", message, NotifyLevel.CRITICAL)


# 全局通知管理器
_notifier_manager: Optional[NotifierManager] = None


def get_notifier() -> NotifierManager:
    """获取全局通知管理器"""
    global _notifier_manager
    if _notifier_manager is None:
        _notifier_manager = NotifierManager()
    return _notifier_manager


# 便捷函数
def notify(title: str, content: str, level: NotifyLevel = NotifyLevel.INFO, symbol: str = None):
    """发送通知"""
    return get_notifier().notify(title, content, level, symbol)

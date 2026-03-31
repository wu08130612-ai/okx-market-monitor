#!/usr/bin/env python3
"""
实时行情监控工具

功能：
- 实时抓取 OKX 持仓信息和委托单
- 委托成交时自动通知
- 持仓跌幅超过 1% 时通知（不含杠杆）
- 实时抓取 OKX 所有加密货币行情
- 检测金叉/死叉信号或高点低点不断抬高的形态
"""
import os
import sys
import time
import logging
import threading
import signal
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    # API
    OKX_API_KEY, OKX_SECRET, OKX_PASSPHRASE,
    # 监控频率
    PRICE_CHECK_INTERVAL,
    POSITION_CHECK_INTERVAL,
    ORDER_CHECK_INTERVAL,
    SIGNAL_CHECK_INTERVAL,
    # 功能开关
    ENABLE_POSITION_MONITOR,
    ENABLE_ORDER_MONITOR,
    ENABLE_SIGNAL_MONITOR,
)
from core.okx_client import OKXClient
from monitors.position_monitor import PositionMonitor
from monitors.order_monitor import OrderMonitor
from monitors.signal_monitor import SignalMonitor
from notifiers.manager import NotifierManager, NotifyLevel

# 日志配置
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "monitor.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class MarketMonitor:
    """
    行情监控主程序

    整合所有监控模块，多线程运行
    """

    def __init__(self):
        """初始化监控程序"""
        # 初始化 OKX 客户端
        self.client = OKXClient(
            api_key=OKX_API_KEY.get(),
            secret=OKX_SECRET.get(),
            passphrase=OKX_PASSPHRASE.get()
        )

        # 初始化通知管理器
        self.notifier = NotifierManager()

        # 初始化监控器
        self.position_monitor = PositionMonitor(self.client, self.notifier)
        self.order_monitor = OrderMonitor(self.client, self.notifier)
        self.signal_monitor = SignalMonitor(self.client, self.notifier)

        # 运行状态
        self.running = False
        self._stop_event = threading.Event()

    def run_position_monitor(self):
        """运行持仓监控线程"""
        while not self._stop_event.is_set():
            try:
                if ENABLE_POSITION_MONITOR:
                    result = self.position_monitor.check_positions()
                    if result["alerts"]:
                        logger.info(f"[持仓监控] 发现 {len(result['alerts'])} 个告警")
            except Exception as e:
                logger.error(f"[持仓监控] 异常: {e}", exc_info=True)

            self._stop_event.wait(POSITION_CHECK_INTERVAL)

    def run_order_monitor(self):
        """运行委托单监控线程"""
        while not self._stop_event.is_set():
            try:
                if ENABLE_ORDER_MONITOR:
                    result = self.order_monitor.check_orders()
                    if result["alerts"]:
                        logger.info(f"[委托监控] 发现 {len(result['alerts'])} 个成交")
            except Exception as e:
                logger.error(f"[委托监控] 异常: {e}", exc_info=True)

            self._stop_event.wait(ORDER_CHECK_INTERVAL)

    def run_signal_monitor(self):
        """运行信号监控线程"""
        while not self._stop_event.is_set():
            try:
                if ENABLE_SIGNAL_MONITOR:
                    result = self.signal_monitor.check_signals()
                    if result["golden_cross"]:
                        logger.info(f"[信号监控] 发现 {len(result['golden_cross'])} 个金叉")
                    if result["death_cross"]:
                        logger.info(f"[信号监控] 发现 {len(result['death_cross'])} 个死叉")
                    if result["uptrend"]:
                        logger.info(f"[信号监控] 发现 {len(result['uptrend'])} 个上升趋势")
            except Exception as e:
                logger.error(f"[信号监控] 异常: {e}", exc_info=True)

            self._stop_event.wait(SIGNAL_CHECK_INTERVAL)

    def start(self):
        """启动监控"""
        logger.info("=" * 60)
        logger.info("实时行情监控工具启动")
        logger.info("=" * 60)

        # 显示配置
        self._show_config()

        # 测试 API 连接
        if not self._test_connection():
            logger.error("API 连接测试失败，请检查配置")
            return

        # 发送启动通知
        self.notifier.notify(
            title="🚀 监控系统启动",
            content="实时行情监控工具已启动，开始监控...",
            level=NotifyLevel.INFO
        )

        self.running = True
        self._stop_event.clear()

        # 初始化订单监控的已知订单
        if ENABLE_ORDER_MONITOR:
            self.order_monitor.init_orders()

        # 启动监控线程
        threads = []

        if ENABLE_POSITION_MONITOR:
            t = threading.Thread(target=self.run_position_monitor, daemon=True, name="PositionMonitor")
            t.start()
            threads.append(t)
            logger.info("[持仓监控] 已启动")

        if ENABLE_ORDER_MONITOR:
            t = threading.Thread(target=self.run_order_monitor, daemon=True, name="OrderMonitor")
            t.start()
            threads.append(t)
            logger.info("[委托监控] 已启动")

        if ENABLE_SIGNAL_MONITOR:
            t = threading.Thread(target=self.run_signal_monitor, daemon=True, name="SignalMonitor")
            t.start()
            threads.append(t)
            logger.info("[信号监控] 已启动")

        # 注册信号处理
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        # 主循环
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到键盘中断...")
            self.stop()

    def stop(self):
        """停止监控"""
        logger.info("正在停止监控...")

        self.running = False
        self._stop_event.set()

        # 发送停止通知
        self.notifier.notify(
            title="🛑 监控系统停止",
            content="实时行情监控工具已停止",
            level=NotifyLevel.WARNING
        )

        logger.info("监控已停止")

    def _handle_signal(self, signum, frame):
        """处理信号"""
        logger.info(f"收到信号 {signum}")
        self.stop()

    def _show_config(self):
        """显示配置信息"""
        logger.info("-" * 40)
        logger.info("配置信息:")
        logger.info(f"  持仓检查间隔: {POSITION_CHECK_INTERVAL}秒")
        logger.info(f"  委托检查间隔: {ORDER_CHECK_INTERVAL}秒")
        logger.info(f"  信号检查间隔: {SIGNAL_CHECK_INTERVAL}秒")
        logger.info(f"  持仓监控: {'启用' if ENABLE_POSITION_MONITOR else '禁用'}")
        logger.info(f"  委托监控: {'启用' if ENABLE_ORDER_MONITOR else '禁用'}")
        logger.info(f"  信号监控: {'启用' if ENABLE_SIGNAL_MONITOR else '禁用'}")
        logger.info("-" * 40)

        # 显示通知渠道
        channels = []
        if self.notifier.notifiers:
            for n in self.notifier.notifiers:
                channels.append(n.__class__.__name__.replace("Notifier", ""))
        if channels:
            logger.info(f"已配置通知渠道: {', '.join(channels)}")
        else:
            logger.warning("未配置任何通知渠道，请在 .env 中配置")

    def _test_connection(self) -> bool:
        """测试 API 连接"""
        try:
            # 测试公共 API
            ticker = self.client.get_ticker("BTC-USDT-SWAP")
            if ticker:
                logger.info(f"API 连接测试成功: BTC 价格 ${float(ticker.get('last', 0)):,.2f}")
                return True
            return False
        except Exception as e:
            logger.error(f"API 连接测试失败: {e}")
            return False


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           实时行情监控工具 v1.0                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  功能:                                                    ║
    ║  • 持仓跌幅监控（超过 1% 通知）                           ║
    ║  • 委托成交通知                                           ║
    ║  • 金叉/死叉信号检测                                      ║
    ║  • 高点低点抬高形态识别                                   ║
    ║  • 多渠道推送（微信/QQ/Gmail/钉钉）                       ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    monitor = MarketMonitor()
    monitor.start()


if __name__ == "__main__":
    main()

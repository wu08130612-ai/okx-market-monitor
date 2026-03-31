#!/usr/bin/env python3
"""
完整通知测试 - 模拟真实信号
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from notifiers.manager import NotifierManager, NotifyLevel
from datetime import datetime

def test_notifications():
    """测试所有通知功能"""
    print("=" * 50)
    print("行情监控系统 - 通知测试")
    print("=" * 50)
    print()

    notifier = NotifierManager()

    if not notifier.notifiers:
        print("❌ 未配置任何通知渠道")
        return

    print(f"已加载 {len(notifier.notifiers)} 个通知渠道")
    print()

    # 测试 1: 系统启动通知
    print("[测试 1] 发送系统启动通知...")
    notifier.notify(
        title="🚀 监控系统启动",
        content="""系统已成功启动，开始监控市场...

功能列表:
• 持仓跌幅监控 (阈值 1%)
• 委托成交通知
• 金叉/死叉信号检测
• 上升趋势形态识别

监控交易对: 全部 USDT 永续合约""",
        level=NotifyLevel.INFO
    )
    print("✅ 已发送")
    print()

    # 测试 2: 模拟持仓跌幅告警
    print("[测试 2] 发送持仓跌幅告警...")
    notifier.notify_position_loss(
        symbol="BTC-USDT-SWAP",
        direction="多仓",
        open_price=85000.00,
        current_price=83500.00,
        loss_pct=0.0176,  # 1.76%
        threshold=0.01
    )
    print("✅ 已发送")
    print()

    # 测试 3: 模拟订单成交
    print("[测试 3] 发送订单成交通知...")
    notifier.notify_order_filled(
        symbol="ETH-USDT-SWAP",
        side="buy",
        price=1850.50,
        amount=0.5,
        order_type="limit"
    )
    print("✅ 已发送")
    print()

    # 测试 4: 模拟金叉信号
    print("[测试 4] 发送金叉信号通知...")
    notifier.notify_signal(
        symbol="SOL-USDT-SWAP",
        signal_type="golden_cross",
        price=145.80,
        details="EMA12 上穿 EMA26，短期趋势转强"
    )
    print("✅ 已发送")
    print()

    # 测试 5: 模拟上升趋势
    print("[测试 5] 发送上升趋势信号...")
    notifier.notify_signal(
        symbol="DOGE-USDT-SWAP",
        signal_type="uptrend",
        price=0.185,
        details="高点抬高 + 低点抬高，形成完整上升趋势结构"
    )
    print("✅ 已发送")
    print()

    print("=" * 50)
    print("✅ 所有测试完成！")
    print("📬 请检查你的邮箱（包括垃圾邮件文件夹）")
    print("=" * 50)


if __name__ == "__main__":
    test_notifications()

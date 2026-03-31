#!/usr/bin/env python3
"""
Gmail 通知测试脚本
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from notifiers.gmail import GmailNotifier
from notifiers.base import NotifyMessage, NotifyLevel
from datetime import datetime

def test_gmail():
    """测试 Gmail 发送"""
    import os

    user = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    to_addr = os.getenv("GMAIL_TO")

    print("=" * 50)
    print("Gmail 通知测试")
    print("=" * 50)
    print(f"发件人: {user}")
    print(f"收件人: {to_addr}")
    print(f"密码长度: {len(password) if password else 0} 字符")
    print()

    if not user or not password or not to_addr:
        print("❌ 配置不完整，请检查 .env 文件")
        return False

    # 创建通知器
    notifier = GmailNotifier(user, password, to_addr)

    # 创建测试消息
    message = NotifyMessage(
        title="🚀 行情监控系统测试",
        content="""**这是一条测试消息**

- 功能: Gmail 通知测试
- 时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
- 状态: 测试成功 ✅

如果你收到这封邮件，说明 Gmail 通知配置成功！""",
        level=NotifyLevel.INFO,
        symbol="BTC-USDT-SWAP"
    )

    print("正在发送测试邮件...")

    try:
        result = notifier.send(message)
        if result:
            print("✅ 邮件发送成功！请检查收件箱（包括垃圾邮件文件夹）")
            return True
        else:
            print("❌ 邮件发送失败")
            return False
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False


if __name__ == "__main__":
    test_gmail()

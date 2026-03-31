#!/usr/bin/env python3
"""
Gmail 发送测试 - 使用标准库 smtplib
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import ssl

def send_test_email():
    """发送测试邮件"""
    # 从环境变量读取配置
    from dotenv import load_dotenv
    load_dotenv()

    sender = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    receiver = os.getenv("GMAIL_TO")

    print("=" * 50)
    print("Gmail 发送测试")
    print("=" * 50)
    print(f"发件人: {sender}")
    print(f"收件人: {receiver}")
    print()

    if not sender or not password or not receiver:
        print("❌ 配置不完整")
        return False

    # 创建邮件
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = "🚀 行情监控系统测试"

    body = f"""
这是一条测试消息

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 行情监控系统通知
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

如果你收到这封邮件，说明 Gmail 通知配置成功！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
此邮件由行情监控系统自动发送
"""

    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        print("正在连接 Gmail SMTP 服务器...")

        # 创建 SSL 上下文
        context = ssl.create_default_context()

        # 连接 Gmail SMTP 服务器
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            print("正在登录...")
            server.login(sender, password)
            print("正在发送邮件...")
            server.sendmail(sender, receiver, message.as_string())

        print()
        print("✅ 邮件发送成功！")
        print("📬 请检查收件箱（或垃圾邮件文件夹）")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print()
        print("❌ 认证失败！")
        print()
        print("可能的原因：")
        print("1. Gmail 需要使用「应用专用密码」，而不是登录密码")
        print("2. 需要开启两步验证")
        print()
        print("解决方法：")
        print("1. 访问 https://myaccount.google.com/security")
        print("2. 开启「两步验证」")
        print("3. 访问 https://myaccount.google.com/apppasswords")
        print("4. 生成一个新的应用专用密码")
        print("5. 将应用专用密码填入 .env 文件")
        print()
        print(f"错误详情: {e}")
        return False

    except Exception as e:
        print()
        print(f"❌ 发送失败: {e}")
        return False


if __name__ == "__main__":
    send_test_email()

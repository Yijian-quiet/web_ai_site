# services/email_service.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")


def send_email(to_email: str, subject: str, body: str) -> bool:
    """发送邮件"""
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html", "utf-8"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


def send_verify_email(to_email: str, username: str, verify_url: str) -> bool:
    """发送验证邮件"""
    subject = "验证你的邮箱 - 不颓废的小健"
    body = f"""
    <div style="max-width:600px;margin:0 auto;padding:20px;font-family:sans-serif;">
        <h2 style="color:#6C63FF;">验证你的邮箱</h2>
        <p>你好 {username}，</p>
        <p>感谢注册「不颓废的小健」！请点击下方按钮验证你的邮箱：</p>
        <a href="{verify_url}" style="display:inline-block;padding:12px 24px;background:#6C63FF;color:#fff;text-decoration:none;border-radius:6px;margin:16px 0;">验证邮箱</a>
        <p style="color:#999;font-size:12px;">如果按钮不可用，请复制以下链接到浏览器：<br>{verify_url}</p>
        <p style="color:#999;font-size:12px;">此链接30分钟内有效。</p>
    </div>
    """
    return send_email(to_email, subject, body)


def send_reset_email(to_email: str, username: str, reset_url: str) -> bool:
    """发送密码重置邮件"""
    subject = "重置密码 - 不颓废的小健"
    body = f"""
    <div style="max-width:600px;margin:0 auto;padding:20px;font-family:sans-serif;">
        <h2 style="color:#6C63FF;">重置密码</h2>
        <p>你好 {username}，</p>
        <p>请点击下方按钮重置你的密码：</p>
        <a href="{reset_url}" style="display:inline-block;padding:12px 24px;background:#6C63FF;color:#fff;text-decoration:none;border-radius:6px;margin:16px 0;">重置密码</a>
        <p style="color:#999;font-size:12px;">如果按钮不可用，请复制以下链接到浏览器：<br>{reset_url}</p>
        <p style="color:#999;font-size:12px;">此链接30分钟内有效。如果不是你本人操作，请忽略此邮件。</p>
    </div>
    """
    return send_email(to_email, subject, body)

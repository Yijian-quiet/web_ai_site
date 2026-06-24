# models/user.py
import bcrypt
from datetime import datetime, timedelta
from utils.db import get_db_connection
from config import LOGIN_MAX_ATTEMPTS, LOGIN_LOCK_MINUTES

# ========================
# 注册
# ========================
def register_user(username, password):
    if not username or not password:
        return False, "用户名和密码不能为空"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False, "用户名已存在"
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash.decode("utf-8"))
        )
        conn.commit()
        return True, "注册成功！"
    finally:
        conn.close()

# ========================
# 登录（纯用户名限流）
# ========================
def is_user_locked(username):
    """检查用户名是否被锁定"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        since = datetime.now() - timedelta(minutes=LOGIN_LOCK_MINUTES)
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM login_attempts WHERE username = %s AND success = 0 AND attempted_at > %s",
            (username, since)
        )
        result = cursor.fetchone()
        return result and result["cnt"] >= LOGIN_MAX_ATTEMPTS
    finally:
        conn.close()

def get_recent_failures(username):
    """统计用户名近15分钟失败次数"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        since = datetime.now() - timedelta(minutes=LOGIN_LOCK_MINUTES)
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM login_attempts WHERE username = %s AND success = 0 AND attempted_at > %s",
            (username, since)
        )
        result = cursor.fetchone()
        return result["cnt"] if result else 0
    finally:
        conn.close()

def record_login_attempt(username, success):
    """记录登录尝试"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO login_attempts (username, ip_address, success) VALUES (%s, %s, %s)",
            (username, "", 1 if success else 0)
        )
        conn.commit()
    finally:
        conn.close()

def clear_login_attempts(username):
    """登录成功后清除旧记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM login_attempts WHERE username = %s", (username,))
        conn.commit()
    finally:
        conn.close()

def verify_user(username, password, ip_address=None):
    """验证登录（ip_address保留兼容但不再用于限流）"""
    try:
        # 检查是否被锁定
        locked = is_user_locked(username)
        if locked:
            remaining_minutes = LOGIN_LOCK_MINUTES
            record_login_attempt(username, False)
            return False, None, f"登录失败次数过多，账号已锁定，请{remaining_minutes}分钟后再试"

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
                record_login_attempt(username, True)
                clear_login_attempts(username)
                return True, user["id"], None
            else:
                record_login_attempt(username, False)
                fail_count = get_recent_failures(username)
                remaining = LOGIN_MAX_ATTEMPTS - fail_count
                msg = "用户名或密码错误！"
                if remaining > 0:
                    msg += f" 还剩 {remaining} 次尝试机会"
                else:
                    msg += f" 账号已锁定 {LOGIN_LOCK_MINUTES} 分钟"
                return False, None, msg
        finally:
            conn.close()
    except Exception as e:
        return False, None, f"登录出错: {str(e)}"

def get_username_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return row["username"] if row else None
    finally:
        conn.close()

def get_admin_status(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return bool(row["is_admin"]) if row else False
    finally:
        conn.close()
# ==== 追加到 models/user.py 的末尾 ====

import secrets
from datetime import datetime, timedelta
from services.email_service import send_verify_email, send_reset_email

def register_user_with_email(username, password, email):
    """注册（含邮箱）"""
    if not username or not password or not email:
        return False, "用户名、密码和邮箱不能为空"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False, "用户名已存在"
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return False, "该邮箱已被注册"
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
            (username, password_hash.decode("utf-8"), email)
        )
        conn.commit()
        user_id = cursor.lastrowid

        # 发送验证邮件（失败不影响注册）
        try:
            token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(hours=1)
            cursor.execute(
                "INSERT INTO email_verifications (user_id, email, token, expires_at) VALUES (%s, %s, %s, %s)",
                (user_id, email, token, expires)
            )
            conn.commit()
            verify_url = f"http://your-domain.com/verify/{token}"
            send_verify_email(email, username, verify_url)
            return True, "注册成功！请检查邮箱完成验证。"
        except Exception:
            return True, "注册成功！（邮箱验证服务暂不可用，稍后可重试）"
    finally:
        conn.close()


def send_password_reset(email):
    """发送密码重置邮件"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return False, "该邮箱未注册"

        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(minutes=30)
        cursor.execute(
            "INSERT INTO password_resets (user_id, token, expires_at) VALUES (%s, %s, %s)",
            (user["id"], token, expires)
        )
        conn.commit()

        reset_url = f"http://your-domain.com/reset-password?token={token}"
        send_reset_email(email, user["username"], reset_url)
        return True, "重置密码链接已发送到你的邮箱"
    finally:
        conn.close()


def reset_password(token, new_password):
    """用 token 重置密码"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, user_id, expires_at, used FROM password_resets WHERE token = %s",
            (token,)
        )
        row = cursor.fetchone()
        if not row:
            return False, "无效的链接"
        if row["used"]:
            return False, "该链接已被使用"
        if row["expires_at"] < datetime.now():
            return False, "链接已过期"

        password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash.decode("utf-8"), row["user_id"])
        )
        cursor.execute("UPDATE password_resets SET used = 1 WHERE id = %s", (row["id"],))
        conn.commit()
        return True, "密码重置成功！请重新登录。"
    finally:
        conn.close()


def verify_email_token(token):
    """验证邮箱"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT user_id, expires_at FROM email_verifications WHERE token = %s AND used = 0",
            (token,)
        )
        row = cursor.fetchone()
        if not row:
            return False, "无效或已使用的验证链接"
        if row["expires_at"] < datetime.now():
            return False, "验证链接已过期"
        cursor.execute("UPDATE users SET email_verified = 1 WHERE id = %s", (row["user_id"],))
        cursor.execute("UPDATE email_verifications SET used = 1 WHERE token = %s", (token,))
        conn.commit()
        return True, "邮箱验证成功！"
    finally:
        conn.close()


def update_email(user_id, new_email):
    """更新邮箱"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET email = %s, email_verified = 0 WHERE id = %s", (new_email, user_id))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_user_email(user_id):
    """获取用户邮箱"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT email, email_verified FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return row if row else None
    finally:
        conn.close()

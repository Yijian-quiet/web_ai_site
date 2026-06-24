# models/admin.py - 管理后台数据查询
from utils.db import get_db_connection


def get_overview_stats():
    """总览统计"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) as cnt FROM users')
        user_count = cursor.fetchone()['cnt']

        cursor.execute('SELECT COUNT(*) as cnt FROM chat_history')
        msg_count = cursor.fetchone()['cnt']

        cursor.execute('SELECT COUNT(DISTINCT session_id) as cnt FROM chat_history')
        session_count = cursor.fetchone()['cnt']

        cursor.execute('SELECT COUNT(*) as cnt FROM chat_history WHERE timestamp >= NOW() - INTERVAL 24 HOUR')
        today_msg = cursor.fetchone()['cnt']

        cursor.execute('SELECT COUNT(DISTINCT user_id) as cnt FROM chat_history WHERE timestamp >= NOW() - INTERVAL 24 HOUR')
        today_users = cursor.fetchone()['cnt']

        return {
            'user_count': user_count,
            'msg_count': msg_count,
            'session_count': session_count,
            'today_msg': today_msg,
            'today_users': today_users,
        }
    finally:
        conn.close()


def get_all_users():
    """获取所有用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT u.id, u.username, u.is_admin, u.created_at,
                   COUNT(ch.id) as msg_count,
                   MAX(ch.timestamp) as last_active
            FROM users u
            LEFT JOIN chat_history ch ON ch.user_id = u.id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        ''')
        return cursor.fetchall()
    finally:
        conn.close()


def get_user_chats(user_id, limit=50):
    """获取指定用户的聊天记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, session_id, role, content, rating, timestamp
            FROM chat_history
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        ''', (user_id, limit))
        return cursor.fetchall()
    finally:
        conn.close()


def get_recent_ratings(limit=20):
    """最近评分记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT ch.id, ch.user_id, u.username, ch.session_id, ch.content, ch.rating, ch.timestamp
            FROM chat_history ch
            JOIN users u ON u.id = ch.user_id
            WHERE ch.rating IS NOT NULL
            ORDER BY ch.timestamp DESC
            LIMIT %s
        ''', (limit,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_msg_trend(days=7):
    """消息趋势（最近N天每日消息数）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT DATE(timestamp) as day, COUNT(*) as cnt
            FROM chat_history
            WHERE timestamp >= NOW() - INTERVAL %s DAY
            GROUP BY DATE(timestamp)
            ORDER BY day
        ''', (days,))
        return cursor.fetchall()
    finally:
        conn.close()


def delete_user(user_id):
    """删除用户及其所有数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM chat_history WHERE user_id = %s', (user_id,))
        cursor.execute('DELETE FROM login_attempts WHERE username IN (SELECT username FROM users WHERE id = %s)', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def set_admin(user_id, is_admin=1):
    """设置管理员权限"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET is_admin = %s WHERE id = %s', (is_admin, user_id))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False
    finally:
        conn.close()

def check_rate_limit(user_id, api_name="chat", max_calls=10, window_minutes=1):
    """检查用户是否超过速率限制，返回 (是否允许, 剩余次数)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(minutes=window_minutes)
        
        # 统计窗口内调用次数
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM rate_limits
            WHERE user_id = %s AND api_name = %s AND called_at > %s
        """, (user_id, api_name, since))
        count = cursor.fetchone()["cnt"]
        
        remaining = max(0, max_calls - count)
        allowed = count < max_calls
        
        # 记录本次调用
        if allowed:
            cursor.execute("""
                INSERT INTO rate_limits (user_id, api_name) VALUES (%s, %s)
            """, (user_id, api_name))
            conn.commit()
        
        return allowed, remaining
    finally:
        conn.close()


def get_rate_limit_stats(user_id=None, window_minutes=60):
    """获取速率限制统计（用于后台）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(minutes=window_minutes)
        
        if user_id:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM rate_limits
                WHERE user_id = %s AND called_at > %s
            """, (user_id, since))
            return {"calls": cursor.fetchone()["cnt"], "window": window_minutes}
        else:
            cursor.execute("""
                SELECT u.username, COUNT(rl.id) as cnt
                FROM rate_limits rl JOIN users u ON u.id = rl.user_id
                WHERE rl.called_at > %s
                GROUP BY rl.user_id ORDER BY cnt DESC
            """, (since,))
            return cursor.fetchall()
    finally:
        conn.close()

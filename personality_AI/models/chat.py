# models/chat.py - MySQL 版
from utils.db import get_db_connection


def save_message(user_id, session_id, role, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO chat_history (user_id, session_id, role, content) VALUES (%s, %s, %s, %s)',
            (user_id, session_id, role, content)
        )
        conn.commit()
        message_id = cursor.lastrowid
        return message_id
    finally:
        conn.close()


def get_all_sessions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT session_id, 
                   MIN(timestamp) as start_time,
                   (SELECT content FROM chat_history h2 
                    WHERE h2.user_id = h1.user_id AND h2.session_id = h1.session_id AND h2.role = 'user'
                    ORDER BY h2.timestamp LIMIT 1) as title
            FROM chat_history h1
            WHERE user_id = %s
            GROUP BY session_id
            ORDER BY start_time DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        sessions = []
        for row in rows:
            title = row['title'] or '新建对话'
            display_title = (title[:20] + '...') if len(title) > 20 else title
            sessions.append({
                'session_id': row['session_id'],
                'title': display_title,
                'start_time': row['start_time']
            })
        return sessions
    finally:
        conn.close()


def save_rating(message_id, rating):   
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE chat_history SET rating = %s WHERE id = %s', (rating, message_id))
        conn.commit()
    finally:
        conn.close()


def delete_session(user_id, session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'DELETE FROM chat_history WHERE user_id = %s AND session_id = %s',
            (user_id, session_id)
        )
        conn.commit()
    finally:
        conn.close()


def load_chat_history_by_session(user_id, session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT id, role, content, timestamp, rating FROM chat_history WHERE user_id = %s AND session_id = %s ORDER BY timestamp ASC',
            (user_id, session_id)
        )
        rows = cursor.fetchall()
        return [
            {
                'id': row['id'],
                'role': row['role'],
                'content': row['content'],
                'timestamp': str(row['timestamp']),
                'rating': row['rating']
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_latest_session_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT session_id FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT 1',
            (user_id,)
        )
        row = cursor.fetchone()
        return row['session_id'] if row else None
    finally:
        conn.close()

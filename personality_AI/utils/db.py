# utils/db.py - MySQL 版（带 DictCursor）
import pymysql
from pymysql.cursors import DictCursor
from config import MYSQL_CONFIG

def get_db_connection():
    """获取 MySQL 数据库连接"""
    config = dict(MYSQL_CONFIG)
    config['cursorclass'] = DictCursor
    return pymysql.connect(**config)

def get_cursor():
    """便捷方法：获取连接和游标"""
    conn = get_db_connection()
    cursor = conn.cursor()
    return conn, cursor

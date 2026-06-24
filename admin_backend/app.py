#!/usr/bin/env python3

import sys, os
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "yijian_AI"))

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql
from pymysql.cursors import DictCursor

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

MYSQL = {
    "host": os.getenv("MYSQL_HOST", "localhost"), "user": "webai",
    "password": os.getenv("MYSQL_PASSWORD", "test123"),
    "database": "web_ai",
    "charset": "utf8mb4", "cursorclass": DictCursor,
}

def db():
    return pymysql.connect(**MYSQL)

def require_admin(f):
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ====== 登录 ======
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash, is_admin FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        conn.close()
        import bcrypt
        if user and user["is_admin"] and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            session["admin_logged_in"] = True
            session["admin_user"] = username
            session["admin_user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="账号/密码错误，或无管理员权限")
    return render_template("login.html")

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ====== 总览 ======
@app.route("/admin/")
@app.route("/admin")
@require_admin
def dashboard():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users"); user_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM chat_history"); msg_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(DISTINCT session_id) as c FROM chat_history"); session_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM chat_history WHERE timestamp >= NOW() - INTERVAL 24 HOUR"); today_msg = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(DISTINCT user_id) as c FROM chat_history WHERE timestamp >= NOW() - INTERVAL 24 HOUR"); today_users = cur.fetchone()["c"]

    cur.execute("SELECT DATE(timestamp) as day, COUNT(*) as c FROM chat_history WHERE timestamp >= NOW() - INTERVAL 7 DAY GROUP BY DATE(timestamp) ORDER BY day")
    trend = [{"day": r["day"].strftime("%m-%d"), "count": r["c"]} for r in cur.fetchall()]

    cur.execute("SELECT u.username, ch.content, ch.rating, ch.timestamp FROM chat_history ch JOIN users u ON u.id = ch.user_id WHERE ch.rating IS NOT NULL ORDER BY ch.timestamp DESC LIMIT 10")
    recent_ratings = cur.fetchall()
    conn.close()
    return render_template("dashboard.html", **locals())

# ====== 用户管理 ======
@app.route("/admin/users")
@require_admin
def users():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT u.id, u.username, u.is_admin, u.created_at, COUNT(ch.id) as msg_count, MAX(ch.timestamp) as last_active FROM users u LEFT JOIN chat_history ch ON ch.user_id = u.id GROUP BY u.id ORDER BY u.created_at DESC")
    users_list = cur.fetchall()
    conn.close()
    return render_template("users.html", users=users_list)

@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@require_admin
def delete_user(user_id):
    if user_id == session.get("admin_user_id"):
        return jsonify({"success": False, "msg": "不能删除自己"})
    conn = db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM chat_history WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM login_attempts WHERE username IN (SELECT username FROM users WHERE id = %s)", (user_id,))
        cur.execute("DELETE FROM users WHERE id = %s AND is_admin = 0", (user_id,))
        conn.commit()
        return jsonify({"success": True if cur.rowcount > 0 else False, "msg": "" if cur.rowcount > 0 else "不能删除管理员"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "msg": str(e)})
    finally:
        conn.close()

@app.route("/admin/users/promote/<int:user_id>", methods=["POST"])
@require_admin
def promote_user(user_id):
    conn = db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET is_admin = 1 WHERE id = %s", (user_id,))
        conn.commit()
        return jsonify({"success": True})
    except:
        conn.rollback()
        return jsonify({"success": False})
    finally:
        conn.close()

# ====== 聊天记录 ======
@app.route("/admin/chats")
@require_admin
def chats():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT id, username FROM users ORDER BY username")
    user_list = cur.fetchall()
    selected_user = request.args.get("user_id", "")
    limit = int(request.args.get("limit", 50))
    messages = []
    if selected_user:
        cur.execute("SELECT role, content, rating, timestamp FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s", (selected_user, limit))
        messages = cur.fetchall()
    conn.close()
    return render_template("chats.html", users=user_list, messages=messages, selected_user=selected_user)
@app.route("/admin/posts")
@require_admin
def blog_posts_list():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT id, title, status, view_count, created_at, updated_at FROM blog_posts ORDER BY created_at DESC")
    posts = cur.fetchall(); conn.close()
    return render_template("posts.html", posts=posts)


@app.route("/admin/posts/new", methods=["GET", "POST"])
@require_admin
def blog_post_new():
    if request.method == "POST":
        title = request.form.get("title", "")
        content = request.form.get("content", "")
        summary = request.form.get("summary", "")
        tags = request.form.get("tags", "")
        status = request.form.get("status", "draft")
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        conn = db(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO blog_posts (user_id, title, slug, content, summary, tags, status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (session["admin_user_id"], title, slug, content, summary, tags, status)
        )
        conn.commit(); conn.close()
        return redirect(url_for("blog_posts_list"))
    return render_template("post_edit.html", post=None)


@app.route("/admin/posts/edit/<int:post_id>", methods=["GET", "POST"])
@require_admin
def blog_post_edit(post_id):
    conn = db(); cur = conn.cursor()
    if request.method == "POST":
        cur.execute(
            "UPDATE blog_posts SET title=%s, content=%s, summary=%s, tags=%s, status=%s WHERE id=%s",
            (request.form["title"], request.form["content"], request.form["summary"], request.form["tags"], request.form["status"], post_id)
        )
        conn.commit(); conn.close()
        return redirect(url_for("blog_posts_list"))
    cur.execute("SELECT * FROM blog_posts WHERE id = %s", (post_id,))
    post = cur.fetchone(); conn.close()
    return render_template("post_edit.html", post=post)


@app.route("/admin/posts/delete/<int:post_id>", methods=["POST"])
@require_admin
def blog_post_delete(post_id):
    conn = db(); cur = conn.cursor()
    cur.execute("DELETE FROM blog_posts WHERE id = %s", (post_id,))
    conn.commit(); conn.close()
    return jsonify({"success": True})


# ====== 个人主页 ======
def _load_json(filename):
    import json, os
    path = os.path.join(os.path.dirname(__file__), "data", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

@app.route("/")
def home():
    profile = _load_json("profile.json")
    return render_template("index.html", profile=profile)

@app.route("/about")
def about():
    profile = _load_json("profile.json")
    timeline = _load_json("timeline.json")
    return render_template("about.html", profile=profile, timeline=timeline)

@app.route("/projects")
def projects():
    projects = _load_json("projects.json")
    return render_template("projects.html", projects=projects)

@app.route("/publications")
def publications():
    publications = _load_json("publications.json")
    return render_template("publications.html", publications=publications)

@app.route("/tools")
def tools():
    tools = _load_json("tools.json")
    return render_template("tools.html", tools=tools)

@app.route("/chat")
def chat_redirect():
    return redirect("http://your-domain.com")


# ====== 公开博客 ======

@app.route("/blog")
def blog_index():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM blog_posts WHERE status='published'")
    total = cur.fetchone()["c"]
    offset = (page - 1) * per_page
    cur.execute("SELECT id, title, slug, summary, tags, view_count, created_at FROM blog_posts WHERE status='published' ORDER BY created_at DESC LIMIT %s OFFSET %s", (per_page, offset))
    posts = cur.fetchall(); conn.close()
    return render_template("blog.html", posts=posts, page=page, total=total, per_page=per_page)


@app.route("/blog/<string:slug>")
def blog_detail(slug):
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT * FROM blog_posts WHERE slug = %s AND status='published'", (slug,))
    post = cur.fetchone()
    if not post:
        cur.execute("SELECT * FROM blog_posts WHERE id = %s", (slug,))
        post = cur.fetchone()
    if not post:
        conn.close()
        return "<h1>404 文章未找到</h1>", 404
    cur.execute("UPDATE blog_posts SET view_count = view_count + 1 WHERE id = %s", (post["id"],))
    conn.commit(); conn.close()
    import markdown
    post["content"] = markdown.markdown(post["content"], extensions=["extra", "codehilite"])
    return render_template("blog_detail.html", post=post)


# ====== 手机版聊天 ======
import uuid as _uuid

@app.route("/m")
def mobile_chat_page():
    return render_template("mobile_chat.html")


@app.route("/m/login", methods=["POST"])
def mobile_login_api():
    import bcrypt, json
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT id, password_hash, is_admin FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"success": True, "user_id": user["id"], "is_admin": bool(user["is_admin"])})
    return jsonify({"success": False, "error": "用户名或密码错误"}), 401


@app.route("/m/history", methods=["POST"])
def mobile_history_api():
    data = request.get_json()
    user_id = data.get("user_id")
    conn = db(); cur = conn.cursor()
    cur.execute(
        "SELECT session_id, MIN(timestamp) as t FROM chat_history WHERE user_id = %s GROUP BY session_id ORDER BY t DESC LIMIT 20",
        (user_id,)
    )
    sessions = []
    for r in cur.fetchall():
        cur.execute("SELECT content FROM chat_history WHERE user_id=%s AND session_id=%s AND role='user' ORDER BY timestamp LIMIT 1", (user_id, r["session_id"]))
        title_row = cur.fetchone()
        title = title_row["content"][:30] if title_row else "新对话"
        sessions.append({"id": r["session_id"][:12], "title": title, "full_id": r["session_id"]})
    conn.close()
    return jsonify(sessions)


@app.route("/m/messages", methods=["POST"])
def mobile_messages_api():
    data = request.get_json()
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT role, content FROM chat_history WHERE user_id=%s AND session_id=%s ORDER BY timestamp",
                (data["user_id"], data["session_id"]))
    msgs = [{"role": r["role"], "content": r["content"]} for r in cur.fetchall()]
    conn.close()
    return jsonify(msgs)


@app.route("/m/chat", methods=["POST"])
def mobile_chat_api():
    data = request.get_json()
    user_id = data["user_id"]
    session_id = data["session_id"]
    message = data["message"]
    from openai import OpenAI
    import os
    client = OpenAI()
    # 保存用户消息
    conn = db(); cur = conn.cursor()
    cur.execute("INSERT INTO chat_history (user_id, session_id, role, content) VALUES (%s, %s, 'user', %s)",
                (user_id, session_id, message))
    conn.commit()
    # 获取历史
    cur.execute("SELECT role, content FROM chat_history WHERE user_id=%s AND session_id=%s ORDER BY timestamp",
                (user_id, session_id))
    history = [{"role": r["role"], "content": r["content"]} for r in cur.fetchall()]
    conn.close()
    # ===== RAG: 检索博客文章作为上下文 =====
    from blog_rag_service import get_blog_context
    blog_ctx, has_blog = get_blog_context(message)
    sys_prompt = "你是不颓废的小健，一个积极乐观的化学AI研究者。"
    if has_blog:
        sys_prompt = blog_ctx + "\n\n请参考以上博客内容回答用户的问题。如果问题与博客无关，忽略这些参考内容。"
    # 调 DeepSeek
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": sys_prompt}] + history[-20:],
        stream=False
    )
    reply = response.choices[0].message.content
    conn = db(); cur = conn.cursor()
    cur.execute("INSERT INTO chat_history (user_id, session_id, role, content) VALUES (%s, %s, 'assistant', %s)",
                (user_id, session_id, reply))
    conn.commit()
    conn.close()
    return jsonify({"reply": reply})


@app.route("/m/new", methods=["POST"])
def mobile_new_session_api():
    return jsonify({"session_id": str(_uuid.uuid4())})


# ====== 邮箱验证 & 密码重置 ======
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'yijian_AI'))
from models.user import verify_email_token, reset_password, send_password_reset
from datetime import datetime

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '')
        success, msg = send_password_reset(email)
        icon = 'OK' if success else 'FAIL'
        return render_template('base_public.html', content=f'<div class="container"><div class="card-glass" style="padding:40px;margin-top:40px;text-align:center;"><h3>{icon} {msg}</h3><p style="margin-top:16px;"><a href="/">返回首页</a></p></div></div>')
    return render_template('forgot_password.html')

@app.route('/verify/<token>')
def verify_email(token):
    success, msg = verify_email_token(token)
    icon = 'OK' if success else 'FAIL'
    return render_template('base_public.html', content=f'<div class="container"><div class="card-glass" style="padding:40px;margin-top:40px;text-align:center;"><h3>{icon} {msg}</h3><p style="margin-top:16px;"><a href="/">返回首页</a></p></div></div>')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_page():
    token = request.args.get('token', '')
    if request.method == 'POST':
        new_pass = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if new_pass != confirm:
            return render_template('base_public.html', content=f'<div class="container"><div class="card-glass" style="padding:40px;margin-top:40px;text-align:center;"><h3>FAIL: 两次密码不一致</h3><p style="margin-top:16px;"><a href="/reset-password?token={token}">重新输入</a></p></div></div>')
        success, msg = reset_password(token, new_pass)
        icon = 'OK' if success else 'FAIL'
        return render_template('base_public.html', content=f'<div class="container"><div class="card-glass" style="padding:40px;margin-top:40px;text-align:center;"><h3>{icon} {msg}</h3><p style="margin-top:16px;"><a href="/chat">去登录</a></p></div></div>')
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)

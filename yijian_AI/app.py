# app.py
import streamlit as st
import uuid
import ollama
from datetime import datetime
from models.user import verify_user, register_user
from models.chat import *
from services.ollama_service import get_ollama_response


st.set_page_config(page_title="不颓废的小健-自由基的AI分身", page_icon="🤖", layout="wide")

def get_installed_models():
    try:
        models = ollama.list()
        return [model['name'] for model in models.get('models', [])]
    except Exception:
        return ["gemma3:4b", "qwen3:4b"]

# 初始化会话状态
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = get_installed_models()[0] if get_installed_models() else "gemma3:4b"
# ========================
# 登录/注册界面
# ========================
def show_auth():
    st.title("🔐 欢迎使用「不颓废的小健」")
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        login_username = st.text_input("用户名", key="login_user")
        login_password = st.text_input("密码", type="password", key="login_pass")
        if st.button("登录"):
            success, user_id = verify_user(login_username, login_password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = login_username
                
                installed = get_installed_models()
                st.session_state.selected_model = installed[0] if installed else "gemma3:4b"
                
                latest_session = get_latest_session_id(user_id)
                if latest_session:
                    st.session_state.current_session_id = latest_session
                    st.session_state.messages = load_chat_history_by_session(user_id, latest_session)
                else:
                    st.session_state.current_session_id = str(uuid.uuid4())
                    st.session_state.messages = []
                    send_welcome_message(st.session_state.selected_model)
                st.rerun()
            else:
                st.error("用户名或密码错误！")
    
    with tab2:
        reg_username = st.text_input("用户名", key="reg_user")
        reg_password = st.text_input("密码", type="password", key="reg_pass")
        reg_confirm = st.text_input("确认密码", type="password", key="reg_confirm")
        if st.button("注册"):
            if reg_password != reg_confirm:
                st.error("两次密码不一致！")
            else:
                success, msg = register_user(reg_username, reg_password)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# ========================
# 发送欢迎消息
# ========================
def send_welcome_message(model_name):
    welcome_prompt = "你好！请向刚刚登录的用户打个招呼，介绍自己是‘不颓废的小健’，并鼓励他开始对话。"
    ai_reply = get_ollama_response([{"role": "user", "content": welcome_prompt}], model_name)
    save_message(st.session_state.user_id, st.session_state.current_session_id, "assistant", ai_reply)
    # 注意：这里不直接设 st.session_state.messages，而是重新加载（含 id）
    st.session_state.messages = load_chat_history_by_session(st.session_state.user_id, st.session_state.current_session_id)

# ========================
# 聊天主界面（已修复评分）
# ========================
def show_chat():
    st.session_state.all_sessions = get_all_sessions(st.session_state.user_id)

    with st.sidebar:
        st.title(f"👤 {st.session_state.username}")
        installed_models = get_installed_models()
        selected = st.selectbox(
            "🧠 选择模型",
            options=installed_models,
            index=installed_models.index(st.session_state.selected_model) if st.session_state.selected_model in installed_models else 0,
            key="model_selector"
        )
        if selected != st.session_state.selected_model:
            st.session_state.selected_model = selected
            st.rerun()
        st.caption(f"当前模型: {st.session_state.selected_model}")

        st.divider()
        if st.button("新建对话", use_container_width=True):
            new_session_id = str(uuid.uuid4())
            st.session_state.current_session_id = new_session_id
            st.session_state.messages = []
            send_welcome_message(st.session_state.selected_model)
            st.rerun()
        
        st.divider()
        st.subheader("💬 历史对话")
        for sess in st.session_state.all_sessions[:20]:
            col_title, col_delete = st.columns([5, 1])
            with col_title:
                if st.button(sess["title"], key=f"load_{sess['session_id']}", use_container_width=True):
                    st.session_state.current_session_id = sess["session_id"]
                    st.session_state.messages = load_chat_history_by_session(st.session_state.user_id, sess["session_id"])
                    st.rerun()
            with col_delete:
                if st.button("🗑️", key=f"del_{sess['session_id']}", help="删除此对话"):
                    st.session_state.confirm_delete = sess["session_id"]
                    st.rerun()

        if "confirm_delete" in st.session_state:
            session_to_delete = st.session_state.confirm_delete
            title = next((s['title'] for s in st.session_state.all_sessions if s['session_id'] == session_to_delete), '该对话')
            st.sidebar.warning(f"确定要删除「{title}」？")
            col_yes, col_no = st.sidebar.columns(2)
            with col_yes:
                if st.button("✅ 确认", key="confirm_yes"):
                    delete_session(st.session_state.user_id, session_to_delete)
                    if st.session_state.current_session_id == session_to_delete:
                        st.session_state.current_session_id = str(uuid.uuid4())
                        st.session_state.messages = []
                        send_welcome_message(st.session_state.selected_model)
                    del st.session_state.confirm_delete
                    st.rerun()
            with col_no:
                if st.button("❌ 取消", key="confirm_no"):
                    del st.session_state.confirm_delete
                    st.rerun()
        if False:
            st.divider()
            with st.expander("📊 模型评分统计"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        SUBSTR(content, 1, 50) as snippet,
                        rating,
                        timestamp
                    FROM chat_history 
                    WHERE user_id = ? AND role = 'assistant' AND rating IS NOT NULL
                    ORDER BY timestamp DESC LIMIT 5
                ''', (st.session_state.user_id,))
                rows = cursor.fetchall()
                conn.close()
                if rows:
                    for row in rows:
                        emoji = {"1": "👎", "2": "👌", "3": "👍"}.get(str(row["rating"]), "❓")
                        st.write(f"{emoji} {row['snippet']}... ({row['timestamp']})")
                else:
                    st.write("暂无评分记录")

        st.divider()
        if st.button("退出登录", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            

    # 主聊天区
    st.title("💬 不颓废的小健 - 自由基的AI分身")
    
    # 渲染所有消息（含评分控件）
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
                st.caption(msg["timestamp"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(msg["content"])
                st.caption(msg["timestamp"])
                # 显示评分状态
                if msg["rating"] is None:
                    col1, col2, col3 = st.columns(3)
                    mid = msg["id"]
                    with col1:
                        if st.button("👍 好", key=f"good_{mid}"):
                            save_rating(mid, 3)
                            st.toast("感谢反馈！😊", icon="✅")
                            st.rerun()
                    with col2:
                        if st.button("👌 一般", key=f"ok_{mid}"):
                            save_rating(mid, 2)
                            st.toast("收到！我们会改进。", icon="ℹ️")
                            st.rerun()
                    with col3:
                        if st.button("👎 不好", key=f"bad_{mid}"):
                            save_rating(mid, 1)
                            st.toast("抱歉！请告诉我们哪里不好？", icon="⚠️")
                            st.rerun()
                else:
                    emoji = {1: "👎", 2: "👌", 3: "👍"}.get(msg["rating"], "❓")
                    st.caption(f"已评：{emoji}")

    # 用户输入
    if prompt := st.chat_input("输入你的问题..."):
        # 保存用户消息
        user_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_message(st.session_state.user_id, st.session_state.current_session_id, "user", prompt)
        
        # 添加到会话
        st.session_state.messages.append({
            "id": None,  # 用户消息不需要评分
            "role": "user",
            "content": prompt,
            "timestamp": user_timestamp,
            "rating": None
        })
        
        # 显示用户消息
        with st.chat_message("user"):
            st.write(prompt)
            st.caption(user_timestamp)
        
        # 获取 AI 回复
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.write("🤔 正在思考...")
            ai_reply = get_ollama_response(
                [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                st.session_state.selected_model
            )
            
            # 保存 AI 消息（获取 id）
            ai_msg_id = save_message(st.session_state.user_id, st.session_state.current_session_id, "assistant", ai_reply)
            ai_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 重新加载整个会话（确保包含新消息的 id 和 rating）
            st.session_state.messages = load_chat_history_by_session(
                st.session_state.user_id, st.session_state.current_session_id
            )
            
            # 显示新消息
            placeholder.write(ai_reply)
            st.caption(ai_timestamp)
            st.rerun()

# ========================
# 主逻辑
# ========================
if not st.session_state.logged_in:
    show_auth()
else:
    show_chat()
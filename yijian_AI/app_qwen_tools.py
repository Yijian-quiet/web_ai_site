# app_qwen.py
import streamlit as st
import uuid
from datetime import datetime
from models.user import verify_user, register_user
from models.chat import *
from services.retro import show_retro_interface  
from services.qwen_service import get_qwen_response, get_qwen_response_stream

st.set_page_config(page_title="不颓废的小健-自由基的AI分身", page_icon="🤖", layout="wide")


# 初始化会话状态
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "chat"
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


# ========================
# 登录/注册界面（保持不变）
# ========================
def show_auth():
    st.title("欢迎来和「不颓废的小健」聊天")
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
                
                latest_session = get_latest_session_id(user_id)
                if latest_session:
                    st.session_state.current_session_id = latest_session
                    st.session_state.messages = load_chat_history_by_session(user_id, latest_session)
                else:
                    st.session_state.current_session_id = str(uuid.uuid4())
                    st.session_state.messages = []
                    send_welcome_message()
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
# 发送欢迎消息（保持不变）
# ========================
def send_welcome_message():
    welcome_prompt = "你好！请向刚刚登录的用户打个招呼，介绍自己是‘不颓废的小健’，并鼓励他开始对话。"
    ai_reply = get_qwen_response([{"role": "user", "content": welcome_prompt}], model="qwen-plus")
    #save_message(st.session_state.user_id, st.session_state.current_session_id, "assistant", ai_reply)
    st.session_state.messages = load_chat_history_by_session(st.session_state.user_id, st.session_state.current_session_id)


# ========================
# 聊天主界面（仅修改侧边栏导航部分）
# ========================
def show_chat():
    st.session_state.all_sessions = get_all_sessions(st.session_state.user_id)

    with st.sidebar:
        st.title(f"👤 {st.session_state.username}")

        st.divider()
        if st.button("新建对话", use_container_width=True):
            new_session_id = str(uuid.uuid4())
            st.session_state.current_session_id = new_session_id
            st.session_state.messages = []
            send_welcome_message()
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
                        send_welcome_message()
                    del st.session_state.confirm_delete
                    st.rerun()
            with col_no:
                if st.button("❌ 取消", key="confirm_no"):
                    del st.session_state.confirm_delete
                    st.rerun()
        
        # ✨ 动态功能导航（关键修改！）
        st.divider()
        st.subheader("可用工具")
        for mode_key in PAGE_REGISTRY:
            if mode_key == "chat":
                continue  # 跳过聊天（已在顶部）
            label = PAGE_LABELS.get(mode_key, mode_key.capitalize())
            if st.button(label, use_container_width=True):
                st.session_state.view_mode = mode_key
                st.rerun()

        # 返回按钮（如果不在聊天页）
        if st.session_state.view_mode != "chat":
            if st.button("↩️ 返回聊天", use_container_width=True):
                st.session_state.view_mode = "chat"
                st.rerun()

        st.divider()
        if st.button("退出登录", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # 主聊天区
    st.title("💬 不颓废的小健 - 自由基的AI分身")
    
    # 渲染历史消息
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
                st.caption(msg["timestamp"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(msg["content"])
                st.caption(msg["timestamp"])
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
        user_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_message(st.session_state.user_id, st.session_state.current_session_id, "user", prompt)
        st.session_state.messages.append({
            "id": None,
            "role": "user",
            "content": prompt,
            "timestamp": user_timestamp,
            "rating": None
        })
        
        with st.chat_message("user"):
            st.write(prompt)
            st.caption(user_timestamp)

        # 仅传 user/assistant 消息，system prompt 由 qwen_service 自动添加
        chat_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
            if m["role"] in ["user", "assistant"]
        ]

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for chunk in get_qwen_response_stream(chat_messages, model="qwen-plus"):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            ai_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.caption(ai_timestamp)

            # 保存完整回复
            ai_msg_id = save_message(st.session_state.user_id, st.session_state.current_session_id, "assistant", full_response)
            st.session_state.messages = load_chat_history_by_session(
                st.session_state.user_id, st.session_state.current_session_id
            )
            st.rerun()
            # ✅ 到此结束，无需 rerun()

# ========================
# 页面注册表（核心！）
# ========================
PAGE_REGISTRY = {
    "chat": show_chat,
    "retro": show_retro_interface,
    # 未来新增页面只需在这里注册，例如：
    # "property": show_property_prediction,
    # "forward": show_forward_synthesis,
}

# 页面显示名称（用于侧边栏）
PAGE_LABELS = {
    "chat": "💬 聊天",
    "retro": "🧪 Retro* 逆合成规划",
    # "property": "📊 分子性质预测",
    # "forward": "➡️ 正向合成",
}


# ========================
# 主逻辑（彻底重构！）
# ========================
def main():
    if not st.session_state.logged_in:
        show_auth()
    else:
        # 从注册表动态获取当前页面函数
        render_func = PAGE_REGISTRY.get(st.session_state.view_mode)
        if render_func is None:
            st.error("❌ 未知页面模式！已自动返回聊天界面。")
            st.session_state.view_mode = "chat"
            st.rerun()
        else:
            render_func()  # 动态调用


if __name__ == "__main__":
    main()
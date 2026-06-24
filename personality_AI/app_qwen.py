# app_qwen.py - 已切换为 DeepSeek API
import streamlit as st
import uuid
from datetime import datetime
from models.user import verify_user, register_user_with_email, get_admin_status
from models.admin import check_rate_limit
from models.chat import *
from services.admin_ui import show_admin_dashboard
from services.deepseek_tools_service import get_response_stream
from services.blog_rag_service import get_blog_context, refresh as refresh_rag

st.set_page_config(page_title="不颓废的小健-自由基的AI分身", page_icon="🤖", layout="wide")


SESSION_DEFAULTS = {
    "view_mode": "chat",
    "logged_in": False,
    "user_id": None,
    "username": "",
    "is_admin": False,
    "messages": [],
    "current_session_id": str(uuid.uuid4()),
    "all_sessions": [],
}

for key, val in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


def get_client_ip():
    try:
        import os
        for var in ("HTTP_X_FORWARDED_FOR", "REMOTE_ADDR"):
            val = os.environ.get(var, "")
            if val:
                return val.split(",")[0].strip() if var == "HTTP_X_FORWARDED_FOR" else val
    except:
        pass
    return "127.0.0.1"


# ======================== 登录/注册 ========================
def show_auth():
    st.title("欢迎来和「不颓废的小健」聊天")
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        login_username = st.text_input("用户名", key="login_user")
        login_password = st.text_input("密码", type="password", key="login_pass")
        st.markdown('<div style="text-align:right;font-size:0.8rem;"><a href="/forgot-password" target="_blank" style="color:#6C63FF;">忘记密码？</a></div>', unsafe_allow_html=True)
        if st.button("登录"):
            success, user_id, error_msg = verify_user(login_username, login_password, get_client_ip())
            if success:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = login_username
                st.session_state.is_admin = get_admin_status(user_id) or False
                
                latest = get_latest_session_id(user_id)
                if latest:
                    st.session_state.current_session_id = latest
                    st.session_state.messages = load_chat_history_by_session(user_id, latest)
                else:
                    st.session_state.current_session_id = str(uuid.uuid4())
                    st.session_state.messages = []
                st.rerun()
            else:
                st.error(error_msg or "用户名或密码错误！")
    
    with tab2:
        reg_username = st.text_input("用户名", key="reg_user")
        reg_password = st.text_input("密码", type="password", key="reg_pass")
        reg_confirm = st.text_input("确认密码", type="password", key="reg_confirm")
        reg_email = st.text_input("邮箱", placeholder="用于密码找回", key="reg_email")
        if st.button("注册"):
            if reg_password != reg_confirm:
                st.error("两次密码不一致！")
            else:
                try:
                    success, msg = register_user_with_email(reg_username, reg_password, reg_email)
                    st.success(msg) if success else st.error(msg)
                except Exception as e:
                    st.error(f"注册失败（邮箱服务暂不可用），请稍后再试或联系管理员")


# ======================== 聊天主界面 ========================
def show_chat():
    st.session_state.all_sessions = get_all_sessions(st.session_state.user_id)

    with st.sidebar:
        st.markdown('<div style="display:flex;gap:0.5rem;flex-wrap:wrap;border-bottom:1px solid #e2e8f0;padding-bottom:0.5rem;margin-bottom:0.5rem"><a href="/blog" style="color:#6366f1;text-decoration:none;font-size:0.85rem">📝 博客</a><a href="/m" style="color:#6366f1;text-decoration:none;font-size:0.85rem">📱 手机版</a></div>', unsafe_allow_html=True)
        st.title(f"👤 {st.session_state.username}")
        if st.session_state.is_admin:
            st.caption("🛡️ 管理员")

        st.divider()
        if st.button("新建对话", use_container_width=True):
            st.session_state.current_session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        st.subheader("💬 历史对话")
        for sess in st.session_state.all_sessions[:20]:
            c1, c2 = st.columns([5, 1])
            with c1:
                if st.button(sess["title"], key=f"load_{sess['session_id']}", use_container_width=True):
                    st.session_state.current_session_id = sess["session_id"]
                    st.session_state.messages = load_chat_history_by_session(st.session_state.user_id, sess["session_id"])
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{sess['session_id']}", help="删除"):
                    st.session_state.confirm_delete = sess["session_id"]
                    st.rerun()

        if "confirm_delete" in st.session_state:
            sid = st.session_state.confirm_delete
            title = next((s["title"] for s in st.session_state.all_sessions if s["session_id"] == sid), "该对话")
            st.sidebar.warning(f"确定删除「{title}」？")
            c1, c2 = st.sidebar.columns(2)
            with c1:
                if st.button("✅ 确认", key="confirm_yes"):
                    delete_session(st.session_state.user_id, sid)
                    if st.session_state.current_session_id == sid:
                        st.session_state.current_session_id = str(uuid.uuid4())
                        st.session_state.messages = []
                    del st.session_state.confirm_delete
                    st.rerun()
            with c2:
                if st.button("❌ 取消", key="confirm_no"):
                    del st.session_state.confirm_delete
                    st.rerun()
        
        st.divider()
        st.subheader("可用工具")
        for key in PAGE_REGISTRY:
            if key == "chat":
                continue
            if key == "admin" and not st.session_state.is_admin:
                continue
            if st.button(PAGE_LABELS.get(key, key.capitalize()), use_container_width=True):
                st.session_state.view_mode = key
                st.rerun()

        if st.session_state.view_mode != "chat":
            if st.button("↩️ 返回聊天", use_container_width=True):
                st.session_state.view_mode = "chat"
                st.rerun()

        st.divider()
        if st.button("退出登录", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # ===== 主聊天区 =====
    st.title("💬 不颓废的小健 - 自由基的AI分身")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            st.caption(msg["timestamp"])
            if msg["role"] == "assistant" and msg["id"]:
                mid = msg["id"]
                if msg["rating"] is None:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("👍 好", key=f"good_{mid}"):
                            save_rating(mid, 3); st.toast("谢谢！😊"); st.rerun()
                    with c2:
                        if st.button("👌 一般", key=f"ok_{mid}"):
                            save_rating(mid, 2); st.toast("收到～"); st.rerun()
                    with c3:
                        if st.button("👎 不好", key=f"bad_{mid}"):
                            save_rating(mid, 1); st.toast("抱歉！"); st.rerun()
                else:
                    rating_emoji = {1: '👎', 2: '👌', 3: '👍'}.get(msg['rating'], '❓')
                    st.caption(f"已评：{rating_emoji}")

    # ===== 输入 + 速率限制 =====
    if prompt := st.chat_input("输入你的问题..."):
        allowed, remaining = check_rate_limit(st.session_state.user_id, "chat", 10, 1)
        if not allowed:
            st.warning("⏱️ 请求太频繁，每分钟限10条，请稍后再试")
            st.stop()

        user_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_message(st.session_state.user_id, st.session_state.current_session_id, "user", prompt)
        st.session_state.messages.append({"id": None, "role": "user", "content": prompt, "timestamp": user_ts, "rating": None})

        with st.chat_message("user"):
            st.write(prompt)
            st.caption(user_ts)

        chat_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] in ("user", "assistant")]

        # ===== 系统人格 =====
        PERSONA = "你是不颓废的小健（Mr.自由基），一个积极乐观的化学AI研究者。回答简洁、有见解、带点幽默。你了解自己的研究经历：逆合成规划（JCTC 2024）、蛋白质设计（ACS SynBio 2024，金奖）、多模态化学模型等。你也要像朋友一样和用户聊天。用中文回复。"
        has_persona = False
        for m in chat_msgs:
            if m.get("role") == "system":
                m["content"] = PERSONA + "\n\n" + m["content"]
                has_persona = True
                break
        if not has_persona:
            chat_msgs.insert(0, {"role": "system", "content": PERSONA})

        # ===== RAG: 检索博客文章作为上下文 =====
        blog_context, has_blog = get_blog_context(prompt)
        if has_blog:
            chat_msgs.insert(0, {"role": "system", "content": blog_context + "\n\n请参考以上博客内容回答用户的问题。如果问题与博客无关，忽略这些参考内容。"})



        with st.chat_message("assistant"):
            placeholder = st.empty()
            full = ""
            for chunk in get_response_stream(chat_msgs):
                full += chunk
                placeholder.markdown(full + "▌", unsafe_allow_html=True)
            placeholder.markdown(full, unsafe_allow_html=True)
            ai_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.caption(ai_ts)
            # 分子图
            _sf = render_smiles_in_text(full)
            for _s, _sv in _sf:
                st.markdown(_sv, unsafe_allow_html=True)
                st.caption(_s)
            save_message(st.session_state.user_id, st.session_state.current_session_id, "assistant", full)
            st.session_state.messages = load_chat_history_by_session(st.session_state.user_id, st.session_state.current_session_id)
            st.rerun()


# ======================== 页面注册表 ========================
PAGE_LABELS = {"chat": "💬 聊天", "admin": "⚙️ 管理后台"}


# ======================== 主逻辑 ========================

# ====== SMILES 可视化 ======
def render_smiles_in_text(text):
    import re
    smiles = re.findall(r'[A-Z][A-Za-z0-9@+\\[\\]()\\/=#:]+', text)
    results = []
    seen = set()
    for s in smiles:
        if s in seen or len(s) < 3 or len(s) > 150:
            continue
        seen.add(s)
        if not re.search(r'[A-Z]', s):
            continue
        if re.match(r'^[A-Z][a-z]{0,2}$', s):
            continue
        if not re.search(r'[0-9\\[\\]()\\/=#@+]', s) and len(s) > 6:
            continue
        if 'http' in s:
            continue
        results.append(s)
        if len(results) >= 5:
            break
    return results

def main():
    if not st.session_state.logged_in:
        show_auth()
    else:
        func = PAGE_REGISTRY.get(st.session_state.view_mode)
        if func is None:
            st.error("❌ 未知页面")
            st.session_state.view_mode = "chat"
            st.rerun()
        else:
            func()


if __name__ == "__main__":
    main()

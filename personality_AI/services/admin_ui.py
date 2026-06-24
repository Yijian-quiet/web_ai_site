# services/admin_ui.py - 管理后台页面
import streamlit as st
from models.admin import (
    get_overview_stats, get_all_users, get_user_chats,
    get_recent_ratings, get_msg_trend, delete_user, set_admin
)


def show_admin_dashboard():
    """管理后台总览页"""
    st.set_page_config(page_title='管理后台', page_icon='⚙️', layout='wide')
    
    st.title('⚙️ 管理后台')

    # 顶部导航
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button('📊 总览', use_container_width=True):
            st.session_state.admin_page = 'overview'
            st.rerun()
    with col2:
        if st.button('👥 用户管理', use_container_width=True):
            st.session_state.admin_page = 'users'
            st.rerun()
    with col3:
        if st.button('💬 聊天记录', use_container_width=True):
            st.session_state.admin_page = 'chats'
            st.rerun()
    with col4:
        if st.button('⭐ 评分反馈', use_container_width=True):
            st.session_state.admin_page = 'ratings'
            st.rerun()
    with col5:
        if st.button('↩️ 返回聊天', use_container_width=True):
            st.session_state.view_mode = 'chat'
            st.rerun()

    if 'admin_page' not in st.session_state:
        st.session_state.admin_page = 'overview'

    # ========== 总览 ==========
    if st.session_state.admin_page == 'overview':
        _show_overview()

    # ========== 用户管理 ==========
    elif st.session_state.admin_page == 'users':
        _show_users()

    # ========== 聊天记录 ==========
    elif st.session_state.admin_page == 'chats':
        _show_chats()

    # ========== 评分反馈 ==========
    elif st.session_state.admin_page == 'ratings':
        _show_ratings()


def _show_overview():
    stats = get_overview_stats()
    
    # 统计卡片
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric('👥 总用户数', stats['user_count'])
    with col2:
        st.metric('💬 总消息数', stats['msg_count'])
    with col3:
        st.metric('📂 总会话数', stats['session_count'])
    with col4:
        st.metric('📊 今日消息', stats['today_msg'])
    with col5:
        st.metric('👤 今日活跃', stats['today_users'])
    
    # 趋势图（最近7天）
    st.subheader('📈 消息趋势（近7天）')
    trend = get_msg_trend(7)
    if trend:
        days = [r['day'].strftime('%m-%d') for r in trend]
        counts = [r['cnt'] for r in trend]
        chart_data = {'日期': days, '消息数': counts}
        st.bar_chart(chart_data, x='日期', y='消息数')
    else:
        st.info('暂无数据')
    
    # 最近评分
    st.subheader('⭐ 最近评分')
    ratings = get_recent_ratings(5)
    if ratings:
        for r in ratings:
            emoji = {1: '👎', 2: '👌', 3: '👍'}.get(r['rating'], '❓')
            st.write(f'{emoji} **{r["username"]}**: {r["content"][:60]}... — {r["timestamp"]}')
    else:
        st.info('暂无评分')


def _show_users():
    st.subheader('👥 用户管理')
    users = get_all_users()
    
    for u in users:
        with st.expander(f"{u['username']} {'🛡️' if u['is_admin'] else ''} — 消息: {u['msg_count']} | 最后活跃: {u['last_active'] or '从未'}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f'ID: {u["id"]}')
                st.write(f'创建: {u["created_at"]}')
            with col2:
                if not u['is_admin']:
                    if st.button(f'设为管理员', key=f'promote_{u["id"]}'):
                        set_admin(u['id'], 1)
                        st.success(f'已将 {u["username"]} 设为管理员')
                        st.rerun()
                else:
                    st.write('✅ 管理员')
            with col3:
                if not u['is_admin']:
                    if st.button(f'删除用户', key=f'del_{u["id"]}', type='secondary'):
                        if delete_user(u['id']):
                            st.success(f'已删除用户 {u["username"]}')
                            st.rerun()
                        else:
                            st.error('删除失败')
                elif u['username'] == st.session_state.username:
                    st.write('👤 当前用户')
    
    if not users:
        st.info('暂无用户')


def _show_chats():
    st.subheader('💬 聊天记录查询')
    
    users = get_all_users()
    user_options = {f"{u['username']} (ID:{u['id']})": u['id'] for u in users}
    
    selected = st.selectbox('选择用户', list(user_options.keys()))
    limit = st.slider('显示条数', 10, 200, 50)
    
    if st.button('查询', type='primary'):
        uid = user_options[selected]
        msgs = get_user_chats(uid, limit)
        
        st.write(f'共 {len(msgs)} 条记录')
        for m in msgs:
            emoji_icon = '🤖' if m['role'] == 'assistant' else '👤'
            rating_show = ''
            if m['rating']:
                rating_show = {1: '👎', 2: '👌', 3: '👍'}.get(m['rating'], '')
            
            with st.chat_message(m['role']):
                st.write(m['content'][:200] + ('...' if len(m['content']) > 200 else ''))
                st.caption(f"{m['timestamp']} | {'⭐ ' + rating_show if rating_show else '未评'}")

            st.divider()


def _show_ratings():
    st.subheader('⭐ 评分反馈')
    ratings = get_recent_ratings(100)
    
    if not ratings:
        st.info('暂无评分记录')
        return
    
    # 统计
    total = len(ratings)
    good = sum(1 for r in ratings if r['rating'] == 3)
    ok = sum(1 for r in ratings if r['rating'] == 2)
    bad = sum(1 for r in ratings if r['rating'] == 1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('👍 好评', good, f'{good/total*100:.0f}%' if total else '')
    with col2:
        st.metric('👌 一般', ok, f'{ok/total*100:.0f}%' if total else '')
    with col3:
        st.metric('👎 差评', bad, f'{bad/total*100:.0f}%' if total else '')
    
    st.divider()
    
    for r in ratings:
        emoji = {1: '👎 差评', 2: '👌 一般', 3: '👍 好评'}.get(r['rating'], '❓')
        st.write(f"**{r['username']}** [{emoji}] — {r['timestamp']}")
        st.write(f"{r['content'][:100]}{'...' if len(r['content']) > 100 else ''}")
        st.divider()

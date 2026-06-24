"""逆合成产品展示 v3 - 路线可视化"""
import streamlit as st
import requests
import json

API = "http://172.17.0.1:5050"

def get_svg(smiles):
    try:
        r = requests.post(API + "/retro/api/render_svg", json={"smiles": smiles}, timeout=5)
        if r.ok:
            svg = r.json().get("svg", "")
            return svg
    except:
        pass
    return None

def show_retro_interface():
    st.title("逆合成路径规划")
    
    # 服务状态
    bb_count = 0
    try:
        h = requests.get(API + "/retro/api/health", timeout=3)
        if h.ok:
            d = h.json()
            bb_count = d.get("building_blocks", 0)
            st.caption(f"模板: {d.get('templates', 0)} | 分子库: {bb_count}")
    except:
        st.warning("服务未连接")
    
    # 预设示例
    try:
        r = requests.get(API + "/retro/api/demo_examples", timeout=3)
        if r.ok:
            st.subheader("预设示例")
            exs = r.json()
            for k, ex in exs.items():
                if st.button(ex["name"], key=k, use_container_width=True):
                    st.session_state.retro_smiles = ex["smiles"]
                    st.rerun()
    except:
        pass
    
    st.subheader("目标分子")
    smi = st.text_input("SMILES", value=st.session_state.get("retro_smiles", ""))
    
    if st.button("开始规划", type="primary") and smi.strip():
        with st.spinner("搜索合成路线..."):
            try:
                resp = requests.post(API + "/retro/api/plan", json={"smiles": smi.strip()}, timeout=60)
                if not resp.ok:
                    st.error(f"API 返回 {resp.status_code}")
                    return
                d = resp.json()
                if not d.get("success"):
                    st.error(d.get("error", "规划失败"))
                    return
                
                st.success("规划完成")
                routes = d.get("routes", [])
                if not routes:
                    st.warning("未找到路线")
                    return
                
                st.subheader(f"找到 {len(routes)} 条路线")
                for i, route in enumerate(routes):
                    path = route["path"]
                    status = route["status"]
                    tmpl = route.get("template", "")
                    
                    label = f"路线 {i+1}: {len(path)-1} 步 [{status}]"
                    with st.expander(label, expanded=i==0):
                        # 展示路线树
                        for step_idx, p in enumerate(path):
                            cols = st.columns([1, 4])
                            with cols[0]:
                                # 获取并显示 SVG
                                svg = get_svg(p)
                                if svg:
                                    st.markdown(f'<div style="width:120px">{svg}</div>', unsafe_allow_html=True)
                                else:
                                    st.code(p[:30], language="text")
                            with cols[1]:
                                st.code(p, language="text")
                                if step_idx == 0:
                                    st.caption("目标分子")
                                else:
                                    info = f"步骤 {step_idx}"
                                    if step_idx == 1 and tmpl:
                                        info += f" | 模板: {tmpl}"
                                    st.caption(info)
                                    # 检查是否可购买
                                    try:
                                        exists = requests.post(API + "/retro/api/plan", 
                                            json={"smiles": p, "max_steps": 1}, timeout=3)
                                        if exists.ok:
                                            ej = exists.json()
                                            for r2 in ej.get("routes", []):
                                                if r2.get("status") == "done" and len(r2["path"]) == 1:
                                                    st.success("可购买")
                                    except:
                                        pass
                        
                        st.markdown("---")
            except Exception as e:
                st.error(str(e))

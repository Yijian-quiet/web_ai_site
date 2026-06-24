"""带 function calling 的 DeepSeek 服务"""
import os, json, requests
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Generator

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1")

# ===== 工具定义 =====
RETRO_TOOL = {
    "type": "function",
    "function": {
        "name": "retrosynthesis_plan",
        "description": "对目标分子进行逆合成路径规划，输入SMILES返回合成路线",
        "parameters": {
            "type": "object",
            "properties": {
                "smiles": {"type": "string", "description": "目标分子的 SMILES，例如 CC(=O)Oc1ccccc1C(=O)O"}
            },
            "required": ["smiles"]
        }
    }
}

RETRO_API = "http://172.17.0.1:5050"

def execute_retrosynthesis(smiles):
    """执行逆合成规划"""
    try:
        resp = requests.post(f"{RETRO_API}/retro/api/plan", json={"smiles": smiles}, timeout=30)
        if resp.ok:
            data = resp.json()
            routes = data.get("routes", [])
            if routes:
                lines = [f"找到 {len(routes)} 条路线:"]
                for i, route in enumerate(routes):
                    path = route["path"]
                    status = route["status"]
                    steps = len(path) - 1
                    lines.append(f"路线{i+1}: {' → '.join(path[:4])} ({steps}步, {status})")
                return "\n".join(lines)
            else:
                return "未找到可行的逆合成路线"
        return f"API 错误: {resp.status_code}"
    except Exception as e:
        return f"规划失败: {str(e)}"


def get_response_with_tools(messages, model="deepseek-chat"):
    """带 function calling 的对话"""
    tools = [RETRO_TOOL]
    
    while True:
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=tools, tool_choice="auto", stream=False
        )
        msg = resp.choices[0].message
        
        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                if tc.function.name == "retrosynthesis_plan":
                    args = json.loads(tc.function.arguments)
                    result = execute_retrosynthesis(args.get("smiles", ""))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    })
        else:
            return msg.content


def get_response_stream(messages, model="deepseek-chat"):
    """流式响应 + function calling"""
    tools = [RETRO_TOOL]
    
    # 第一次调用
    resp = client.chat.completions.create(
        model=model, messages=messages, tools=tools, tool_choice="auto", stream=True
    )
    
    tool_calls = {}
    full_content = ""
    
    for chunk in resp:
        delta = chunk.choices[0].delta if chunk.choices else None
        if not delta:
            continue
        if delta.content:
            full_content += delta.content
            yield delta.content
        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls:
                    tool_calls[idx] = {"id": tc.id or "", "name": tc.function.name or "", "args": ""}
                if tc.id:
                    tool_calls[idx]["id"] = tc.id
                if tc.function.name:
                    tool_calls[idx]["name"] = tc.function.name
                if tc.function.arguments:
                    tool_calls[idx]["args"] += tc.function.arguments
    
    if tool_calls:
        # 如果 AI 调用了工具，执行并第二次调用
        yield "\n\n🔬 正在调用逆合成引擎...\n\n"
        messages.append({"role": "assistant", "content": full_content if full_content else None, "tool_calls": [
            {"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["args"]}}
            for tc in tool_calls.values()
        ]})
        
        for tc in tool_calls.values():
            if tc["name"] == "retrosynthesis_plan":
                args = json.loads(tc["args"])
                result = execute_retrosynthesis(args.get("smiles", ""))
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
                messages.append({"role": "system", "content": "请始终使用 SMILES 格式（如 CC(=O)O）表示分子，不要使用传统化学式。在回复中保留 SMILES 以便分子结构渲染"})
        
        # 第二次调用，让 AI 用自然语言解读结果
        resp2 = client.chat.completions.create(
            model=model, messages=messages, stream=True
        )
        # 渲染分子图
        if tool_calls and len(tool_calls) > 0:
            for _tc in tool_calls.values():
                if _tc["name"] == "retrosynthesis_plan":
                    import requests as _rq
                    _args = json.loads(_tc["args"])
                    _smi = _args.get("smiles", "")
                    if _smi:
                        _svg_resp = _rq.post("http://172.17.0.1:5050/retro/api/render_svg", json={"smiles": _smi}, timeout=10)
                        if _svg_resp.ok:
                            _svg = _svg_resp.json().get("svg", "")
                            if _svg:
                                yield "\n\n**分子结构图：**\n"
                                yield f"<div style=\"margin:10px 0;\">{_svg}</div>"
        for chunk in resp2:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    elif full_content:
        yield full_content

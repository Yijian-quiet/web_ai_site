# services/deepseek_service.py
import os
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from typing import List, Dict, Generator
from pathlib import Path

# ========================
# Persona 加载
# ========================
PERSONA_FILE = Path("persona/zhangyijian_persona.txt")
PERSONA_FILE.parent.mkdir(exist_ok=True)

def load_persona():
    if PERSONA_FILE.exists():
        return PERSONA_FILE.read_text(encoding="utf-8")
    else:
        default_persona = """
        你是张一健（小健）的AI分身，名为"不颓废的小健"。
        你是一个积极、务实的技术爱好者，喜欢用简单语言解释复杂问题。
        保持友好、诚实，不知道就说"我不清楚"。
        """
        PERSONA_FILE.write_text(default_persona.strip(), encoding="utf-8")
        return default_persona

# ========================
# DeepSeek 客户端初始化
# ========================
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
)

# ========================
# 非流式函数
# ========================
def get_deepseek_response(messages: List[Dict[str, str]], model: str = "deepseek-chat") -> str:
    try:
        SYSTEM_PROMPT = load_persona()
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] in ["user", "assistant"]
        ]
        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            stream=False,
            timeout=30
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ DeepSeek API 调用失败: {str(e)}"

# ========================
# 流式函数
# ========================
def get_deepseek_response_stream(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    timeout: int = 30
) -> Generator[str, None, None]:
    try:
        SYSTEM_PROMPT = load_persona()
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] in ["user", "assistant"]
        ]
        stream = client.chat.completions.create(
            model=model,
            messages=full_messages,
            stream=True,
            timeout=timeout,
            stream_options={"include_usage": False}
        )
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
    except OpenAIError as e:
        yield f"❌ DeepSeek API 错误: {str(e)}"
    except Exception as e:
        yield f"❌ 未知错误: {str(e)}"

# services/ollama_service.py
import ollama
from config import PERSONA_FILE

def load_persona():
    if PERSONA_FILE.exists():
        return PERSONA_FILE.read_text(encoding="utf-8")
    else:
        default_persona = """
        你是张一健（小健）的AI分身，名为“不颓废的小健”。
        你是一个积极、务实的技术爱好者，喜欢用简单语言解释复杂问题。
        保持友好、诚实，不知道就说“我不清楚”。
        """
        PERSONA_FILE.write_text(default_persona.strip(), encoding="utf-8")
        return default_persona

def get_ollama_response(messages, model_name):
    try:
        SYSTEM_PROMPT = load_persona()
        ollama_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                ollama_messages.append({"role": msg["role"], "content": msg["content"]})
        response = ollama.chat(
            model=model_name,
            messages=ollama_messages,
            options={"temperature": 0.7}
        )
        return response["message"]["content"]
    except Exception as e:
        return f"❌ 调用 Ollama 出错：{str(e)}\n\n请确保 Ollama 正在运行且模型 `{model_name}` 已加载。"
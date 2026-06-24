FROM python:3.11-slim

WORKDIR /app

# 使用清华 PyPI 镜像（比官方快得多）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
RUN pip install --no-cache-dir streamlit pymysql bcrypt openai python-dotenv fastembed onnxruntime

COPY . .
ENV HF_ENDPOINT=https://hf-mirror.com
RUN mkdir -p persona .streamlit

EXPOSE 8501
CMD ["streamlit", "run", "app_qwen.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.maxUploadSize=10"]

"""
博客 RAG 检索服务 v2 — 语义嵌入版
- 稠密向量: BAAI/bge-small-zh-v1.5 (512维, fastembed ONNX)
- 语义匹配，不再关键词硬匹配
- 自动检测文章更新（对比文章数）
- 纯 ONNX 推理，无 PyTorch 依赖
"""
import os, math, re
from typing import List, Dict, Tuple
import pymysql
from pymysql.cursors import DictCursor

# 设置 HF 镜像（中国大陆加速）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from fastembed import TextEmbedding

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "mysql"),
    "port": 3306,
    "user": "webai",
    "password": os.getenv("MYSQL_PASSWORD", "test123"),
    "database": "web_ai",
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
}


# ========== 数据层 ==========

def fetch_posts() -> List[Dict]:
    """从 MySQL 拉取所有已发布文章"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, content, summary, tags, created_at "
                "FROM blog_posts WHERE status='published' ORDER BY id"
            )
            rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[RAG] MySQL 连接失败: {e}")
        return []


def count_published() -> int:
    """快速查询已发布文章数"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as c FROM blog_posts WHERE status='published'")
            result = cur.fetchone()
        conn.close()
        return result["c"] if result else 0
    except:
        return -1


def chunk_post(post: Dict) -> List[Dict]:
    """将文章按 ## 标题分块"""
    content = post["content"]
    title = post["title"]
    chunks = []
    sections = re.split(r'(?=^## )', content, flags=re.MULTILINE)
    for section in sections:
        section = section.strip()
        if not section or len(section) < 20:
            continue
        header_match = re.match(r'^## (.+)', section)
        section_title = header_match.group(1).strip() if header_match else "概述"
        chunks.append({
            "post_id": post["id"],
            "post_title": title,
            "section_title": section_title,
            "text": section,
            "tags": post.get("tags", ""),
        })
    return chunks


# ========== 向量检索引擎 ==========

class DenseVectorStore:
    """稠密向量存储 + 余弦相似度检索（纯 Python，无 FAISS 依赖）"""
    
    def __init__(self):
        self.vectors: List[List[float]] = []
        self.chunks: List[Dict] = []
    
    def add(self, chunks: List[Dict], vectors: List[List[float]]):
        self.chunks = chunks
        self.vectors = vectors
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        if na * nb == 0:
            return 0.0
        return dot / (na * nb)
    
    def search(self, query_vec: List[float], top_k: int = 3, min_score: float = 0.5) -> List[Dict]:
        """检索最相似的 top_k 个分块"""
        if not self.vectors:
            return []
        
        scored = [(self._cosine_similarity(query_vec, v), i) for i, v in enumerate(self.vectors)]
        scored.sort(reverse=True)
        
        results = []
        for score, idx in scored:
            if score < min_score:
                break
            if len(results) >= top_k:
                break
            c = self.chunks[idx]
            results.append({
                "score": round(score, 4),
                "post_title": c["post_title"],
                "section_title": c["section_title"],
                "content": c["text"][:500],
                "full_content": c["text"],
            })
        return results


# ========== RAG 引擎 ==========

class BlogRAGEngine:
    """语义 RAG 检索引擎"""
    
    def __init__(self, min_score: float = 0.5):
        self.min_score = min_score
        self.chunks = []
        self.vector_store = DenseVectorStore()
        self._embed_model = None
        self._initialized = False
        self._known_count = 0
    
    @property
    def embed_model(self):
        if self._embed_model is None:
            print("[RAG] 加载嵌入模型 BAAI/bge-small-zh-v1.5...")
            self._embed_model = TextEmbedding("BAAI/bge-small-zh-v1.5")
            print("[RAG] 嵌入模型就绪")
        return self._embed_model
    
    def check_refresh(self):
        """检测文章是否有更新，自动重建索引"""
        try:
            new_count = count_published()
            if new_count >= 0 and new_count != self._known_count:
                print(f"[RAG] 检测到文章数变化: {self._known_count} -> {new_count}，重建索引...")
                self._initialized = False
                self.initialize()
        except Exception as e:
            print(f"[RAG] 自动刷新检查失败: {e}")
    
    def initialize(self):
        """构建索引：拉取文章 → 分块 → 向量化"""
        posts = fetch_posts()
        if not posts:
            print("[RAG] 没有找到博客文章")
            self._known_count = 0
            return
        
        self.chunks = []
        for post in posts:
            self.chunks.extend(chunk_post(post))
        
        if not self.chunks:
            print("[RAG] 文章分块为空")
            self._known_count = len(posts)
            return
        
        # 批量嵌入
        texts = [c["text"] for c in self.chunks]
        print(f"[RAG] 正在向量化 {len(texts)} 个分块...")
        vectors = list(self.embed_model.embed(texts, show_progress_bar=False))
        
        self.vector_store.add(self.chunks, [list(v) for v in vectors])
        self._known_count = len(posts)
        self._initialized = True
        print(f"[RAG] 初始化完成: {len(posts)} 篇文章 → {len(self.chunks)} 个分块, 嵌入维度 {len(vectors[0])}")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """语义检索"""
        if not self._initialized:
            return []
        query_vec = list(self.embed_model.embed([query], show_progress_bar=False))[0]
        return self.vector_store.search(query_vec, top_k=top_k, min_score=self.min_score)
    
    def format_context(self, query: str) -> str:
        """检索并格式化为 system prompt 上下文"""
        results = self.search(query, top_k=3)
        if not results:
            return ""
        parts = ["以下是博客文章中与你问题相关的内容：\n"]
        for i, r in enumerate(results, 1):
            parts.append(f"[{i}] 文章《{r['post_title']}》- 章节「{r['section_title']}」(相关度{r['score']})")
            parts.append(r["full_content"][:800])
            parts.append("")
        return "\n".join(parts)


# ========== 全局单例 ==========

_engine = None

def get_rag_engine() -> BlogRAGEngine:
    global _engine
    if _engine is None:
        _engine = BlogRAGEngine()
        _engine.initialize()
    return _engine


def get_blog_context(query: str) -> Tuple[str, bool]:
    """获取博客上下文（自动检测更新）"""
    engine = get_rag_engine()
    engine.check_refresh()
    if not engine._initialized:
        return "", False
    context = engine.format_context(query)
    return context, bool(context)


def refresh():
    """强制刷新索引"""
    global _engine
    _engine = None
    get_rag_engine()
    print("[RAG] 索引已刷新")

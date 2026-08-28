# -*- coding: utf-8 -*-
"""向量库公共助手：embedding、分块、入库三件套。

默认使用本地 Chroma（零成本），配置了 PINECONE_API_KEY 时切换到 Pinecone。
"""

import json
from pathlib import Path

from openai import OpenAI

from src.core.config import PROJECT_ROOT, get_settings

#: 单块最大 token 数（法律条文/论文摘要统一切块标准）
MAX_CHUNK_TOKENS = 512


def get_openai_client() -> OpenAI:
    """构造 OpenAI 兼容客户端（读取统一配置）。"""
    settings = get_settings()
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量文本向量化，返回与输入同序的向量列表。"""
    settings = get_settings()
    client = get_openai_client()
    resp = client.embeddings.create(
        model=settings.embedding_model, input=texts
    )
    return [item.embedding for item in resp.data]


def chunk_text(text: str, max_tokens: int = MAX_CHUNK_TOKENS) -> list[str]:
    """按字符近似切分为 <=512 token 的块（中文 1 token≈1 字符，取保守值 480 字）。"""
    step = 480
    return [text[i:i + step] for i in range(0, len(text), step)] if text else []


def get_chroma_collection(name: str):
    """获取（或创建）本地 Chroma 集合。"""
    import chromadb

    settings = get_settings()
    persist_dir = str((PROJECT_ROOT / settings.chroma_persist_dir).resolve())
    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def build_index(corpus_path: Path, collection_name: str) -> int:
    """读取 JSON 语料文件并全部入库，返回入库块数。

    语料 JSON 格式：[{"id": "...", "text": "...", "metadata": {...}}, ...]
    """
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    collection = get_chroma_collection(collection_name)

    texts, ids, metadatas = [], [], []
    for item in corpus:
        for idx, chunk in enumerate(chunk_text(item["text"])):
            texts.append(chunk)
            ids.append(f'{item["id"]}#{idx}')
            metadatas.append(item.get("metadata", {}))

    if not texts:
        raise ValueError(f"语料为空：{corpus_path}")

    vectors = embed_texts(texts)
    collection.upsert(ids=ids, documents=texts, embeddings=vectors, metadatas=metadatas)
    return len(texts)

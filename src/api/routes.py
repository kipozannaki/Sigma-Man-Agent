# -*- coding: utf-8 -*-
"""API 路由：SSE 流式对话、截图脱敏上传、健康检查。"""

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.core.engine import ChatEngine, handle_message
from src.core.profile_cache import ProfileCache
from src.core.state_manager import StateManager
from src.schemas.dimension_weights import DimensionWeights
from src.schemas.score_result import ChatRequest
from src.utils.ocr_processor import process_receipt

logger = logging.getLogger("api")

router = APIRouter()

#: 引擎与缓存均为无状态/连接级单例，进程内复用
engine = ChatEngine()
cache = ProfileCache()


@router.get("/health")
async def health() -> dict:
    """健康检查：验证 Redis 连通性（LLM 延迟由运维脚本探测）。"""
    try:
        await cache.redis.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    status = "ok" if redis_ok else "degraded"
    return {"status": status, "redis": redis_ok, "llm_model": engine.settings.llm_model}


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """SSE 流式对话：追问与最终裁决均以 text/event-stream 返回。"""
    # 用户自定义权重先过归一化校验
    weights = request.weights
    if weights:
        try:
            weights = DimensionWeights(**weights).to_dict()
        except Exception as err:
            raise HTTPException(status_code=422, detail=f"权重非法：{err}")

    # 会话状态恢复或新建
    context = await cache.load_context(request.session_id) or {"weights": weights}
    state = StateManager()
    state.answers = context.get("answers", {})
    state.state = next(
        (s for s in type(state.state) if s.value == context.get("state", "INIT")),
        state.state,
    )

    async def event_generator():
        """SSE 生成器：逐块推送回复，结束后持久化会话状态。"""
        reply = ""
        try:
            # LLM 同步调用放入线程池，避免阻塞事件循环
            reply = await asyncio.to_thread(
                handle_message, engine, state, context, request
            )
            # 按行切块推送，模拟流式体验
            for i in range(0, len(reply), 64):
                yield f"data: {json.dumps({'delta': reply[i:i + 64]}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.02)
        except Exception as err:
            logger.exception("chat_stream_failed session_hash_set=true")
            yield f"data: {json.dumps({'error': '内部推理失败，请稍后重试'}, ensure_ascii=False)}\n\n"
            raise HTTPException(status_code=500, detail=str(err)) from err
        finally:
            # 持久化状态与已答内容（TTL 由缓存层统一控制）
            context.update({"state": state.state.value, "answers": state.answers})
            await cache.save_context(request.session_id, context)
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/upload/receipt")
async def upload_receipt(file: UploadFile) -> dict:
    """截图上传：本地 OCR 提取金额与关键词，原图字节流即弃。"""
    image_bytes = await file.read()
    # OCR 放线程池执行（CPU 密集）
    result = await asyncio.to_thread(process_receipt, image_bytes)
    return {"extracted": result, "privacy": "原图未落盘，已丢弃字节流"}

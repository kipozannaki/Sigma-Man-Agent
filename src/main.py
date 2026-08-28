# -*- coding: utf-8 -*-
"""应用入口：uvicorn sigma-man-agent:main --reload
启动命令：uvicorn src.main:app --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(
    title="sigma-man-agent",
    description="男性情感决策军师 Agent：七困局路由 → 五层追问 → 五维评分 → 红黄绿灯裁决",
    version="1.0.0",
)

# 前端本地联调跨域放行（生产环境收敛到具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

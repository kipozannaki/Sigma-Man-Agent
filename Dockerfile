# sigma-man-agent 后端镜像（Python slim）
FROM python:3.11-slim

# OCR 中文语言包（pytesseract 依赖系统级 tesseract）
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先拷依赖清单利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷源码
COPY src ./src
COPY data ./data
COPY tests ./tests

EXPOSE 8000

# 健康检查由 docker-compose 层定义
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

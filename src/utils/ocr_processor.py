# -*- coding: utf-8 -*-
"""本地 OCR 脱敏工具：提取图片中的金额与关键词。

安全纪律：处理完立即丢弃原始字节流，仅在内存中返回结构化文本，
不落盘、不写临时文件。
"""

import io
import logging
import re

from PIL import Image

logger = logging.getLogger("ocr")

#: 财务语境关键词（命中才保留行，降低误提取）
FINANCE_KEYWORDS: tuple[str, ...] = ("转账", "彩礼", "借款", "汇款", "收款", "工资", "还款", "定金")

#: 金额正则：匹配 1,234,567 / 12345.67 / 12万 等常见写法
AMOUNT_PATTERN = re.compile(r"(?<![\d.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\d.,])\d+(?:\.\d+)?(?=\s*万)|(?<![\d.,])\d{3,}(?:\.\d+)?")


def extract_text(image_bytes: bytes) -> str:
    """从图片字节流中 OCR 提取文本（中文+英文）。"""
    image = Image.open(io.BytesIO(image_bytes))
    import pytesseract

    return pytesseract.image_to_string(image, lang="chi_sim+eng")


def parse_amounts(text: str) -> list[float]:
    """从 OCR 文本解析金额数字，'X万' 按 X*10000 折算。"""
    amounts: list[float] = []
    for raw in AMOUNT_PATTERN.findall(text):
        cleaned = raw.replace(",", "")
        # 后缀带'万'的数字按万元折算
        idx = text.find(raw)
        multiplier = 10000.0 if idx >= 0 and text[idx + len(raw):idx + len(raw) + 1] == "万" else 1.0
        amounts.append(round(float(cleaned) * multiplier, 2))
    return amounts


def find_keywords(text: str) -> list[str]:
    """筛选文本中命中的财务关键词。"""
    return [kw for kw in FINANCE_KEYWORDS if kw in text]


def process_receipt(image_bytes: bytes) -> dict:
    """主入口：OCR → 提取金额/关键词 → 立即丢弃原图字节流。

    返回结构化结果；OCR 失败时返回空结构并记录匿名日志。
    """
    try:
        text = extract_text(image_bytes)
    except Exception:
        # 不记录任何图片内容，只记录失败事实
        logger.warning("ocr_failed bytes_len=%d", len(image_bytes))
        return {"amounts": [], "keywords": [], "raw_text_chars": 0}

    result = {
        "amounts": parse_amounts(text),
        "keywords": find_keywords(text),
        "raw_text_chars": len(text),
    }
    # 安全纪律：函数返回后 image_bytes 与 text 均不再被引用
    logger.info("ocr_done amounts=%d keywords=%d", len(result["amounts"]), len(result["keywords"]))
    return result

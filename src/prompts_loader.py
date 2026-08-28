# -*- coding: utf-8 -*-
"""Prompt 文件加载器：统一从 src/prompts 目录读取文本与追问树 JSON。"""

import json
from functools import lru_cache
from pathlib import Path

#: Prompt 根目录（src/prompts）
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


@lru_cache
def load_prompt(relative_path: str) -> str:
    """读取 prompt 文本文件（带缓存，SSOT：文件内容唯一来源）。"""
    return (PROMPTS_DIR / relative_path).read_text(encoding="utf-8")


@lru_cache
def load_question_tree(scenario: str) -> dict:
    """读取指定场景的追问树 JSON，并校验 5 层递进无循环。"""
    tree_file = PROMPTS_DIR / "question_trees" / f"{scenario.lower()}_tree.json"
    tree = json.loads(tree_file.read_text(encoding="utf-8"))
    depths = [node["depth"] for node in tree["tree"]]

    # 校验：depth 必须恰好为 1..5 递增
    if depths != [1, 2, 3, 4, 5]:
        raise ValueError(f"{tree_file.name} 的追问深度非法：{depths}")
    return tree

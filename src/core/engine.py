# -*- coding: utf-8 -*-
"""核心推理引擎：串联 状态机 × Prompt链 × LLM。

一次会话的完整链路：
INIT → 场景分类 → 5层追问（含敷衍反弹）→ 五维评分 → 红黄绿灯裁决
"""

import json
from pathlib import Path

from src.core.config import PROJECT_ROOT, get_settings
from src.core.guardrails import GUARD_MESSAGE, is_blocked
from src.core.state_manager import ChatState, StateManager
from src.prompts_loader import load_prompt, load_question_tree
from src.schemas.dimension_weights import DEFAULT_WEIGHTS, DimensionWeights
from src.schemas.score_result import ChatRequest, ClassifyResult, ScoreResult

#: 敷衍回答特征：过短或明显回避
EVASION_KEYWORDS = ("不知道", "忘了", "算了", "无所谓", "不想说", "都行", "随便")
MIN_ANSWER_LEN = 6

#: 场景未知时的兜底追问
FALLBACK_QUESTION = "信息太少了。用一句话描述：这段关系里最让你睡不着觉的具体事件是什么？"


class ChatEngine:
    """单例引擎：无状态方法 + 外部传入会话状态（状态机实例存于缓存层）。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = None  # 延迟初始化，避免单测环境强依赖网络

    # ---------- LLM 基础调用 ----------

    def _get_client(self):
        """懒加载 OpenAI 客户端。"""
        if self.client is None:
            from openai import OpenAI

            self.client = OpenAI(
                api_key=self.settings.llm_api_key, base_url=self.settings.llm_base_url
            )
        return self.client

    def _chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        """调用 LLM 并返回纯文本回复。"""
        resp = self._get_client().chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    # ---------- 各阶段 Prompt 驱动 ----------

    def classify(self, first_message: str) -> ClassifyResult:
        """场景路由：LLM 输出 JSON → 强校验。"""
        system = load_prompt("router/scenario_classifier.txt")
        raw = self._chat(system, first_message)
        data = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        return ClassifyResult.model_validate(data)

    def ask_question(self, scenario: str, depth: int) -> str:
        """获取指定场景第 depth 层追问。"""
        tree = load_question_tree(scenario)
        return tree["tree"][depth - 1]["question"]

    def get_bounce_back(self, scenario: str, depth: int) -> str:
        """获取敷衍回答时的反弹话术（引用历史案例施压）。"""
        tree = load_question_tree(scenario)
        return tree["tree"][depth - 1]["bounce_back"]

    def is_evasive(self, answer: str) -> bool:
        """判断用户回答是否敷衍：过短或命中回避关键词。"""
        if len(answer.strip()) < MIN_ANSWER_LEN:
            return True
        return any(kw in answer for kw in EVASION_KEYWORDS)

    def score(self, dialogue_facts: str, weights: dict[str, float]) -> ScoreResult:
        """五维评分：注入用户权重因子，输出强校验 ScoreResult。"""
        system = load_prompt("calculators/pentad_scorer.txt")
        system = system.replace("{custom_weights}", json.dumps(weights, ensure_ascii=False))
        raw = self._chat(system, dialogue_facts, temperature=0.2)
        data = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        return ScoreResult.model_validate(data)

    def verdict(self, score: ScoreResult) -> str:
        """红黄绿灯合成器：输出含行动清单的 Markdown 裁决。"""
        system = load_prompt("synthesizer/final_verdict.txt")
        return self._chat(system, score.model_dump_json(), temperature=0.3)


# ---------- 会话级编排（供路由层调用） ----------

async def handle_message(engine: ChatEngine, state: StateManager, context: dict,
                         request: ChatRequest) -> str:
    """处理单条消息，返回回复文本（同步 LLM 调用由路由层包线程池）。"""
    # 护栏优先：命中即中断全部推理
    if is_blocked(request.message):
        state.state = ChatState.RESULT
        return GUARD_MESSAGE

    if state.state == ChatState.INIT:
        return _start_scenario(engine, state, context, request.message)

    if state.state.name.startswith("QUESTION_Q"):
        return _handle_question(engine, state, context, request.message)

    return "本轮咨询已结束。如需重新评估，请开启新会话。"


def _start_scenario(engine: ChatEngine, state: StateManager, context: dict,
                    message: str) -> str:
    """首条消息：场景分类 → 进入第一层追问。"""
    try:
        result = engine.classify(message)
        scenario = result.scenario.value
    except Exception:
        # 分类失败兜底：直接追问补充信息
        state.advance()
        return FALLBACK_QUESTION

    context["scenario"] = scenario
    state.advance()  # → SCENARIO_MATCH
    state.advance()  # → QUESTION_Q1
    return f"已定位困局：{scenario}。{engine.ask_question(scenario, 1)}"


def _handle_question(engine: ChatEngine, state: StateManager, context: dict,
                     message: str) -> str:
    """追问阶段：敷衍反弹 / 答非所问回退 / 正常推进。"""
    scenario = context.get("scenario", "FINANCE")
    depth = state.depth

    if engine.is_evasive(message):
        # 敷衍：留在当前层，用反弹话术施压
        return engine.get_bounce_back(scenario, depth)

    state.record_answer(depth, message)
    state.advance()
    return _next_action(engine, state, context, message)


def _next_action(engine: ChatEngine, state: StateManager, context: dict,
                 last_answer: str) -> str:
    """推进后分发：继续追问 / 进入评分。"""
    if state.state.name.startswith("QUESTION_Q"):
        return engine.ask_question(context["scenario"], state.depth)

    # 进入 CALCULATING：汇总 5 层回答交给评分器（weights 默认均衡权重）
    weights = context.get("weights") or DEFAULT_WEIGHTS
    facts = "\n".join(f"Q{d}: {a}" for d, a in sorted(state.answers.items()))
    try:
        score = engine.score(facts, weights)
        context["score"] = score.model_dump()
    except Exception:
        state.rollback()
        return "评分数据不足，请补充上一个问题的回答。"

    state.advance()  # → RESULT
    return engine.verdict(score)

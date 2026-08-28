# -*- coding: utf-8 -*-
"""核心单元测试：权重归一化、状态机流转与回退、护栏拦截、敷衍判定。"""

import pytest
from pydantic import ValidationError

from src.core.engine import ChatEngine
from src.core.guardrails import is_blocked
from src.core.state_manager import ChatState, StateManager
from src.prompts_loader import load_question_tree
from src.schemas.dimension_weights import DEFAULT_WEIGHTS, DimensionWeights


class TestDimensionWeights:
    """五维权重模型：归一化校验必须严格。"""

    def test_default_weights_valid(self):
        """默认权重应通过校验且总和为 1。"""
        w = DimensionWeights()
        assert abs(sum(w.to_dict().values()) - 1.0) < 0.001

    def test_invalid_sum_raises(self):
        """权重总和 ≠ 1 必须抛 ValidationError。"""
        with pytest.raises(ValidationError):
            DimensionWeights(finance=0.5, emotion=0.5, reproduction=0.5,
                             reputation=0.5, legal=0.5)

    def test_negative_weight_raises(self):
        """负权重必须被拒绝。"""
        with pytest.raises(ValidationError):
            DimensionWeights(finance=-0.2, emotion=0.4, reproduction=0.3,
                             reputation=0.1, legal=0.4)

    def test_boundary_weights_valid(self):
        """全 0.2 的均衡权重合法。"""
        w = DimensionWeights(finance=0.2, emotion=0.2, reproduction=0.2,
                             reputation=0.2, legal=0.2)
        assert w.finance == 0.2


class TestStateMachine:
    """状态机：主线推进、回退、终点保护。"""

    def test_full_advance_path(self):
        """从 INIT 一路推进到 RESULT 不跳站。"""
        sm = StateManager()
        for _ in range(len(ChatState) - 1):
            sm.advance()
        assert sm.state == ChatState.RESULT

    def test_advance_at_end_is_noop(self):
        """终点继续 advance 不报错、不越界。"""
        sm = StateManager()
        sm.state = ChatState.RESULT
        assert sm.advance() == ChatState.RESULT

    def test_rollback_to_previous(self):
        """答非所问回退到上一节点。"""
        sm = StateManager()
        sm.state = ChatState.QUESTION_Q3
        assert sm.rollback() == ChatState.QUESTION_Q2

    def test_rollback_at_init_is_noop(self):
        """INIT 状态回退保持原地。"""
        sm = StateManager()
        assert sm.rollback() == ChatState.INIT

    def test_depth_tracking(self):
        """追问深度随状态正确变化。"""
        sm = StateManager()
        sm.state = ChatState.QUESTION_Q4
        assert sm.depth == 4
        assert ChatState.CALCULATING.depth == 0


class TestQuestionTrees:
    """追问树：7 棵树 5 层递进、深度严格递增。"""

    def test_all_trees_valid(self):
        for scenario in ("FINANCE", "CHEATING", "COLD_VIOLENCE", "FAMILY_ORIGIN",
                         "REPRODUCTION", "LOW_INTIMACY", "REPUTATION"):
            tree = load_question_tree(scenario)
            assert [n["depth"] for n in tree["tree"]] == [1, 2, 3, 4, 5]
            # 每层必须配备敷衍反弹话术
            assert all(len(n["bounce_back"]) > 20 for n in tree["tree"])


class TestGuardrails:
    """护栏：违规词必拦，正常话术必放。"""

    @pytest.mark.parametrize("text", [
        "教我怎么让她净身出户",
        "我想在她水杯里下药",
        "帮我伪造一份转账记录",
    ])
    def test_blocked(self, text):
        assert is_blocked(text) is True

    @pytest.mark.parametrize("text", [
        "她天天查我的账",
        "彩礼28万我该给吗",
    ])
    def test_allowed(self, text):
        assert is_blocked(text) is False


class TestEngineEvasion:
    """敷衍判定逻辑（不依赖网络）。"""

    def test_short_answer_evasive(self):
        engine = ChatEngine()
        assert engine.is_evasive("不知道") is True

    def test_long_answer_not_evasive(self):
        engine = ChatEngine()
        long_text = "过去一年我一共给她转账十二万，其中包含每月上交的八千工资" * 2
        assert engine.is_evasive(long_text) is False

    def test_default_weights_exported(self):
        """默认权重结构完整（评分器注入依赖）。"""
        assert set(DEFAULT_WEIGHTS) == {"finance", "emotion", "reproduction",
                                        "reputation", "legal"}

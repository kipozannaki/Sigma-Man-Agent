# -*- coding: utf-8 -*-
"""构建心理学语料索引（集合名：psych_db）。

语料来源：戈特曼婚姻研究、依恋理论、煤气灯效应等公开学术概念摘要。
用法：python -m src.utils.build_psych_index
"""

import json
from pathlib import Path

from src.utils.vector_store import build_index

#: 心理学种子语料（公开学术概念的通俗化摘要，便于向量召回）
PSYCH_CORPUS: list[dict] = [
    {
        "id": "gottman_four_horsemen",
        "text": "戈特曼'末日四骑士'（The Four Horsemen of the Apocalypse）：约翰·戈特曼通过长达数十年的婚姻观察实验发现，四种沟通模式对离婚的预测准确率超过90%——批评（criticism，对人格的整体攻击）、蔑视（contempt，讽刺、翻白眼、居高临下，是四骑士中杀伤力最强者）、防御（defensiveness，推卸责任反戈一击）、筑墙（stonewalling，拒绝回应单方面关闭沟通）。研究要点：蔑视不仅预示离婚，还与接收方免疫力下降相关；修复的关键是用'温和启动'替代批评、用文化欣赏替代蔑视、承担责任替代防御、按暂停但约定回归时间替代筑墙。",
        "metadata": {"source": "Gottman Institute 公开研究综述", "topic": "末日四骑士"},
    },
    {
        "id": "attachment_anxious_avoidant",
        "text": "依恋理论与'焦虑-回避陷阱'：成人依恋研究（Hazan & Shaver, 1987 将鲍尔比依恋理论扩展至成人亲密关系）把关系中的不安全感分为焦虑型与回避型。焦虑型通过频繁确认'你爱不爱我'缓解恐惧，回避型通过拉开距离维持自主感——两者结合时形成自我强化的追逃循环：一方追得越紧，另一方退得越远，双方都把对方的策略当作问题本源。识别要点：冷战、已读不回、忽冷忽热常是回避型策略而非'不爱'的直接证据；但长期单方面消耗同样构成关系失衡，需要用'结构化沟通'（定时定量、议题清单）打破循环而非单纯加大情感投入。",
        "metadata": {"source": "成人依恋研究综述", "topic": "焦虑-回避陷阱"},
    },
    {
        "id": "gaslighting_definition",
        "text": "煤气灯效应（Gaslighting）：词源自1944年电影《煤气灯下》，经心理学家 Robin Stern 与 Istvan 等人的研究进入学术语境，指一种系统性心理操纵：操纵者通过否认事实（'你记错了'）、孤立信息源（'你朋友都针对我'）、重新定义受害者的感受（'你太敏感了'），使受害者逐步怀疑自己的记忆、判断与现实感知力。三阶段模型：欺骗（被误导）→ 防御（怀疑自己）→ 抑郁（放弃自我判断权）。识别信号：你开始频繁道歉、开始为对方的行为找借口、开始在开口前预演对方反应。核心反制：保留外部记录（日记、聊天记录）作为'现实锚点'，恢复第三方视角。",
        "metadata": {"source": "心理学文献综述（Robin Stern 等）", "topic": "煤气灯效应"},
    },
    {
        "id": "social_exchange_theory",
        "text": "社会交换理论（Social Exchange Theory，Thibaut & Kelley, 1959）：亲密关系可建模为收益-成本账户，关系满意度=所得-成本，但是否持续取决于'比较水平'（与个人过去经验比较）与'替代比较水平'（与可能的替代选择比较）。关键推论：一段高成本关系可能因'替代选项看起来更差'或'前期投入巨大'而维持，这正是沉没成本谬误的温床。应用：评估关系时必须同时计算三个数——当前净收益、离开的真实成本、留在关系内的机会成本（放弃的更好可能性）。",
        "metadata": {"source": "社会心理学教科书综述", "topic": "社会交换理论"},
    },
    {
        "id": "intermittent_reinforcement",
        "text": "间歇性强化（Intermittent Reinforcement）：源自斯金纳的操作性条件反射实验——不定时、不定额的奖励比稳定奖励更能成瘾性地塑造行为。在亲密关系中表现为'忽冷忽热'：偶尔的温柔与持续的冷漠交替出现，使被控制方像赌徒拉杆一样持续投入以追逐奖励峰值。识别要点：如果你发现自己'为了一次难得的好脸色可以忍受两周的冷淡'，关系已进入间歇性强化结构。反制策略：将评价标准从'峰值体验'改为'基线体验'——看关系 80% 时间的常态质量。",
        "metadata": {"source": "行为心理学综述", "topic": "间歇性强化"},
    },
    {
        "id": "sunk_cost_relationship",
        "text": "沉没成本谬误在关系决策中的表现：'都在一起五年了，现在分不值'——已投入的时间、金钱、情感不会因继续投入而收回，理性决策只应基于未来现金流（这段关系未来的净收益）。行为经济学实验（Arkes & Blumer, 1985）证明人在已投入高的项目中系统性高估成功概率。关系决策校准法：问自己'如果我今天刚认识她，以现在的行为模式，我会选择开始这段关系吗？'——答案是否定的，投入年限不应成为继续的理由。",
        "metadata": {"source": "行为经济学综述", "topic": "沉没成本"},
    },
    {
        "id": "darvo_tactic",
        "text": "DARVO 反转策略（Deny, Attack, Reverse Victim and Offender）：Jennifer Freyd 提出的常见冲突反制话术——被指责任者第一步否认（'没有这事'），第二步攻击指控者（'你就是疑心病'），第三步反转受害者与加害者位置（'你这样查我才是伤害我们的感情'）。效果是指责者陷入自我怀疑并为'怀疑'本身道歉。识别方法：聚焦事实核查而不接情绪战——每轮只问'这件事是真是假'，拒绝进入'谁态度更差'的新战场。",
        "metadata": {"source": "Freyd 等心理学研究", "topic": "DARVO"},
    },
    {
        "id": "triangulation",
        "text": "三角化（Triangulation，家族系统理论，Bowen）：冲突双方不直接解决分歧，而是引入第三方（父母、闺蜜、孩子）形成三角，使冲突结构稳定化但永不被解决。典型表现：'我妈说…''我朋友都觉得你…'。危害：第三方介入使简单分歧升级为阵营对抗。反制：识别并拒绝三角化——'这件事是我们俩的事，我们直接谈'；在原生家庭介入型冲突中，夫妻同盟优先于各自血亲联盟是唯一健康结构。",
        "metadata": {"source": "Bowen 家庭系统理论综述", "topic": "三角化"},
    },
]


def main() -> None:
    """入口：落盘语料 → 向量化入库 → 自检查询。"""
    corpus_file = PROJECT_ROOT / "data" / "raw" / "psych_corpus.json"
    corpus_file.parent.mkdir(parents=True, exist_ok=True)
    corpus_file.write_text(
        json.dumps(PSYCH_CORPUS, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    count = build_index(corpus_file, collection_name="psych_db")
    print(f"[psych_db] 入库完成，共 {count} 个文本块")

    # 自检：'打压自尊' 应能召回煤气灯效应定义
    from src.utils.vector_store import embed_texts, get_chroma_collection

    collection = get_chroma_collection("psych_db")
    result = collection.query(query_embeddings=embed_texts(["打压自尊"]), n_results=2)
    print("[psych_db] 自检查询'打压自尊'召回：")
    for doc in result["documents"][0]:
        print(" -", doc[:60].replace("\n", " "))


if __name__ == "__main__":
    main()

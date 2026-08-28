# -*- coding: utf-8 -*-
"""构建法条向量索引（集合名：legal_db）。

语料来源：《民法典》婚姻家庭编核心条文 + 彩礼返还司法解释 + 典型判决模式。
用法：python -m src.utils.build_legal_index
"""

import json
from pathlib import Path

from src.utils.vector_store import build_index

#: 法条种子语料（正文均为公开法律条文原文摘要）
LEGAL_CORPUS: list[dict] = [
    {
        "id": "civil_code_1042",
        "text": "《民法典》第一千零四十二条：禁止包办、买卖婚姻和其他干涉婚姻自由的行为。禁止借婚姻索取财物。禁止重婚。禁止有配偶者与他人同居。禁止家庭暴力。禁止家庭成员间的虐待和遗弃。本条是处理彩礼纠纷、经济控制类案件的核心请求权基础之一：以结婚为条件索取大额财物且明显超出给付方承受能力的，可主张返还。",
        "metadata": {"source": "民法典婚姻家庭编", "topic": "彩礼与禁止性规定"},
    },
    {
        "id": "civil_code_1064",
        "text": "《民法典》第一千零六十四条：夫妻双方共同签名或者夫妻一方事后追认等共同意思表示所负的债务，以及夫妻一方在婚姻关系存续期间以个人名义为家庭日常生活需要所负的债务，属于夫妻共同债务。夫妻一方在婚姻关系存续期间以个人名义超出家庭日常生活需要所负的债务，不属于夫妻共同债务；但是，债权人能够证明该债务用于夫妻共同生活、共同生产经营或者基于夫妻双方共同意思表示的除外。适用场景：一方擅自举债、被追加为共同借款人、'被负债'风险的隔离判断。",
        "metadata": {"source": "民法典婚姻家庭编", "topic": "夫妻共同债务"},
    },
    {
        "id": "judicial_jielireturn",
        "text": "《最高人民法院关于适用〈民法典〉婚姻家庭编的解释（一）》第五条：当事人请求返还按照习俗给付的彩礼的，如果查明属于以下情形，人民法院应当予以支持：（一）双方未办理结婚登记手续；（二）双方办理结婚登记手续但确未共同生活；（三）婚前给付并导致给付人生活困难。适用前款第二项、第三项的规定，应当以双方离婚为条件。关键词：彩礼返还条件、返还比例考量因素（共同生活时间、过错、孕育情况）。",
        "metadata": {"source": "婚姻家庭编司法解释（一）", "topic": "彩礼返还条件"},
    },
    {
        "id": "civil_code_1079",
        "text": "《民法典》第一千零七十九条：夫妻一方要求离婚的，可以由有关组织进行调解或者直接向人民法院提起离婚诉讼。有下列情形之一，调解无效的，应当准予离婚：（一）重婚或者与他人同居；（二）实施家庭暴力或者虐待、遗弃家庭成员；（三）有赌博、吸毒等恶习屡教不改；（四）因感情不和分居满二年；（五）其他导致夫妻感情破裂的情形。经人民法院判决不准离婚后，双方又分居满一年，一方再次提起离婚诉讼的，应当准予离婚。",
        "metadata": {"source": "民法典婚姻家庭编", "topic": "离婚法定事由"},
    },
    {
        "id": "civil_code_1088",
        "text": "《民法典》第一千零八十八条：夫妻一方因抚育子女、照料老年人、协助另一方工作等负担较多义务的，离婚时有权向另一方请求补偿，另一方应当给予补偿。具体办法由双方协议；协议不成的，由人民法院判决。要点：家务补偿不以'分别财产制'为前提，全职带娃一方在离婚时可主张经济补偿。",
        "metadata": {"source": "民法典婚姻家庭编", "topic": "家务劳动补偿"},
    },
    {
        "id": "civil_code_1091",
        "text": "《民法典》第一千零九十一条：有下列情形之一，导致离婚的，无过错方有权请求损害赔偿：（一）重婚；（二）与他人同居；（三）实施家庭暴力；（四）虐待、遗弃家庭成员；（五）有其他重大过错。要点：'其他重大过错'为兜底条款，长期与他人保持不正当关系、恶意转移财产等情形司法实践中已有支持先例；无过错方需注意合法取证（不得侵犯他人隐私权与通讯自由）。",
        "metadata": {"source": "民法典婚姻家庭编", "topic": "离婚损害赔偿"},
    },
    {
        "id": "case_pattern_caili",
        "text": "典型判决模式（彩礼类，2021-2025 公开裁判文书归纳）：短婚未育（共同生活不足一年）+ 大额彩礼（10万以上）情形下，法院通常判决部分返还，返还比例常见区间为30%-70%，酌定因素包括：共同生活时长、是否孕育子女、彩礼用途（是否置办共同生活用品）、双方过错程度。纯未登记结婚的婚约财产纠纷，返还比例普遍更高。检索关键词：婚约财产纠纷、彩礼返还。",
        "metadata": {"source": "裁判文书公开数据归纳", "topic": "彩礼返还判决模式"},
    },
    {
        "id": "case_pattern_debt",
        "text": "典型判决模式（'被负债'类）：配偶一方以个人名义对外举债，出借人主张夫妻共同债务的，法院重点审查三点：借款是否用于共同生活（消费记录、资金流向）、举债后家庭是否实际受益、非举债方是否事后追认（微信聊天中承认'我们一起还'可能被认定为追认）。风险提示：婚姻存续期间对共同债务纠纷保持沉默≠免责，明确否认并留存书面记录是关键动作。",
        "metadata": {"source": "裁判文书公开数据归纳", "topic": "共同债务认定"},
    },
    {
        "id": "civil_code_1087",
        "text": "《民法典》第一千零八十七条：离婚时，夫妻的共同财产由双方协议处理；协议不成的，由人民法院根据财产的具体情况，按照照顾子女、女方和无过错方权益的原则判决。对夫或者妻在家庭土地承包经营中享有的权益等，应当依法予以保护。要点：无过错方原则在财产分割中已获得明文倾斜，与第1091条损害赔偿构成双重保护。",
        "metadata": {"source": "民法典婚姻家庭编", "topic": "离婚财产分割"},
    },
]


def dump_seed_corpus(output_path: Path) -> None:
    """把内置语料落盘为 JSON（便于增量补充外部判决书后重建索引）。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    corpus = [
        {"id": item["id"], "text": item["text"], "metadata": item["metadata"]}
        for item in LEGAL_CORPUS
    ]
    output_path.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    """入口：落盘语料 → 向量化入库 → 自检查询。"""
    corpus_file = PROJECT_ROOT / "data" / "raw" / "legal_corpus.json"
    dump_seed_corpus(corpus_file)

    count = build_index(corpus_file, collection_name="legal_db")
    print(f"[legal_db] 入库完成，共 {count} 个文本块")

    # 自检：'彩礼返还条件' 应能召回司法解释第五条
    from src.utils.vector_store import embed_texts, get_chroma_collection

    collection = get_chroma_collection("legal_db")
    result = collection.query(query_embeddings=embed_texts(["彩礼返还条件"]), n_results=2)
    print("[legal_db] 自检查询'彩礼返还条件'召回：")
    for doc in result["documents"][0]:
        print(" -", doc[:60].replace("\n", " "))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""检索问答编排 v8：课程识别 + 跨课程引导 + 通用知识兜底 + 重点高亮"""
from app.vector_store import TfidfStore
from app import llm
import config


def detect_course(query):
    """
    识别问题所属课程。
    返回 (course_key, score) 或 (None, 0) 表示无法判断。
    """
    scores = {}
    for course_key, info in config.COURSES.items():
        keywords = info.get("keywords", [])
        score = sum(1 for kw in keywords if kw in query)
        scores[course_key] = score

    if not scores:
        return None, 0

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return None, 0
    return best, scores[best]


PROMPT_TMPL = """你是《{course_name}》课程的答疑助手。请严格依据下方"课程资料片段"回答学生问题。

LaTeX 公式格式要求（必须严格遵守）：
1. 公式用 $$...$$ 包裹，独占一行，前后各空一行。
2. 禁止 \\vec，矢量用 \\mathbf。
3. 行内小符号用 $...$。
4. 禁止方括号 [] 包裹公式。

重点高亮要求：
- 重要的结论、关键概念、核心公式说明，用 **粗体** 标注（将以红色高亮显示）。
- 每个要点至少标注一处 **重点**。

回答要求：
- 优先使用资料片段，引用标注 [1][2]；
- 资料中没有直接答案的宏观/概览性问题，用自身知识回答，末尾"## 来源说明"注明"综合课程概况，非资料片段直接引用"；
- 末尾"## 引用来源"列出：编号. 文档名(第X页)。

课程资料片段：
{context}

学生问题：{query}"""

GENERAL_PROMPT = """你是《{course_name}》课程的答疑助手。学生问了一个课程资料中没有直接涉及的问题。

请用你的专业知识给出清晰回答。

格式要求：
1. 公式用 $$...$$ 包裹，独占一行，禁止 \\vec，矢量用 \\mathbf。
2. 重要的结论、关键概念用 **粗体** 标注（将以红色高亮显示）。

末尾标注"## 来源说明"，注明"综合课程概况，非资料片段直接引用"。

学生问题：{query}"""


def build_context(hits):
    return "\n\n".join(
        f"[{i}] {h['doc']} 第{h['page']}页\n{h['text']}"
        for i, h in enumerate(hits, 1))


def answer(query, store=None, top_k=None, course=None,
           course_name="工程电磁场"):
    # ===== 第一步：跨课程检测 =====
    detected, score = detect_course(query)
    if detected and detected != course and score >= 2:
        other_label = config.COURSES[detected]["label"]
        redirect_msg = (
            f"您的问题与《{other_label}》课程相关，请您移步到"
            f"【{other_label}】答疑模块，可以为您提供更详细的答疑内容。"
        )
        return {
            "answer": redirect_msg,
            "sources": [],
            "redirect": True,
            "redirect_to": detected,
            "redirect_label": other_label,
        }

    # ===== 第二步：检索当前课程资料 =====
    store = store or TfidfStore.load()
    hits = store.search(query, top_k or config.TOP_K, course=course)

    if hits and hits[0]["score"] > 0.1:
        prompt = PROMPT_TMPL.format(
            context=build_context(hits), query=query,
            course_name=course_name)
        text = llm.chat([{"role": "user", "content": prompt}])
        sources = [{"no": i, "doc": h["doc"], "page": h["page"],
                    "score": h["score"], "text": h["text"]}
                   for i, h in enumerate(hits, 1)]
        return {"answer": text, "sources": sources}

    # ===== 第三步：通用知识兜底 =====
    prompt = GENERAL_PROMPT.format(course_name=course_name, query=query)
    text = llm.chat([{"role": "user", "content": prompt}])
    return {"answer": text, "sources": []}
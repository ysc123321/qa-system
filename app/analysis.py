# -*- coding: utf-8 -*-
"""错题解析模块 v8：课程识别 + 跨课程引导 + 通用知识兜底 + 重点高亮"""
import config
from app.vector_store import TfidfStore
from app import llm
from app.qa import detect_course

MISTAKE_PROMPT = """你是《{course_name}》课程的错题解析助教。
请根据下方"课程资料片段"和学生的错题，生成错题解析报告。

格式要求：
1. 公式用 $$...$$ 包裹，独占一行，禁止 \\vec，矢量用 \\mathbf。
2. 行内小符号用 $...$。
3. 关键错因、核心公式、重要结论必须用 **粗体** 标注（系统将以红色高亮显示）。
4. 每个章节至少标注2处 **重点**。

严格按以下结构输出：
## 错因分析
## 正确解法
## 涉及知识点
## 知识点来源

课程资料片段：
{context}

学生错题：
{mistake}"""

GENERAL_MISTAKE_PROMPT = """你是《{course_name}》课程的错题解析助教。
学生的错题在课程资料中没有直接涉及，请用专业知识生成解析报告。

格式要求：
1. 公式用 $$...$$ 包裹，独占一行，禁止 \\vec，矢量用 \\mathbf。
2. 关键错因、核心公式、重要结论必须用 **粗体** 标注（系统将以红色高亮显示）。
3. 每个章节至少标注2处 **重点**。

严格按以下结构输出：
## 错因分析
## 正确解法
## 涉及知识点
## 来源说明
（注明"综合专业知识，非资料片段直接引用"）

学生错题：
{mistake}"""


def analyze_mistake(mistake_text, store=None, top_k=6, course=None,
                    course_name="工程电磁场"):
    # ===== 跨课程检测 =====
    detected, score = detect_course(mistake_text)
    if detected and detected != course and score >= 2:
        other_label = config.COURSES[detected]["label"]
        redirect_msg = (
            f"该错题与《{other_label}》课程相关，请您移步到"
            f"【{other_label}】错题解析模块，可以为您提供更详细的解析。"
        )
        return {
            "report": redirect_msg,
            "sources": [],
            "redirect": True,
            "redirect_to": detected,
            "redirect_label": other_label,
        }

    # ===== 正常解析 =====
    store = store or TfidfStore.load()
    hits = store.search(mistake_text, top_k, course=course)

    if hits and hits[0]["score"] > 0.1:
        context = "\n\n".join(
            f"[{i}] {h['doc']} 第{h['page']}页\n{h['text']}"
            for i, h in enumerate(hits, 1))
        prompt = MISTAKE_PROMPT.format(
            context=context, mistake=mistake_text,
            course_name=course_name)
        report = llm.chat([{"role": "user", "content": prompt}])
        sources = [{"no": i, "doc": h["doc"], "page": h["page"],
                    "score": h["score"], "text": h["text"]}
                   for i, h in enumerate(hits, 1)]
        return {"report": report, "sources": sources}

    prompt = GENERAL_MISTAKE_PROMPT.format(
        course_name=course_name, mistake=mistake_text)
    report = llm.chat([{"role": "user", "content": prompt}])
    return {"report": report, "sources": []}
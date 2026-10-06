# -*- coding: utf-8 -*-
"""水墨风格课程答疑系统 v4：全元素可读 + 重点高亮 + 跨课程引导 + 图片识别"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import glob
import json
import html as html_mod
import streamlit as st
import config
from app.qa import answer
from app.analysis import analyze_mistake
from app.vision import extract_text_from_image

st.set_page_config(page_title="课程智能答疑", layout="wide", page_icon="🏮")

# ====================== 水墨风格 CSS（全元素可读版） ======================
st.markdown("""
<style>
/* =============================================
   第一层：全局所有文字 → 深色（保证可读）
   ============================================= */
* {
    color: #2c2c2c !important;
}

/* =============================================
   第二层：问题区域特殊元素 → 深色
   （expander、summary、pre、输入框、label等）
   ============================================= */
summary, summary *,
details, details *,
pre, pre *, code, code *,
.stTextArea textarea, .stTextInput input,
.stSelectbox [data-baseweb="select"],
div[data-testid="stWidgetLabel"] label,
.stRadio label, .stRadio label span,
.stFileUploader, .stFileUploader *,
.stFileUploader [data-testid="stFileUploaderDropzone"],
.stFileUploader [data-testid="stFileUploaderDropzone"] *,
.stAlert, .stAlert *, .stInfo, .stInfo *,
.stWarning, .stWarning *, .stSuccess, .stSuccess *,
.stCaption, .stCaption *, .stCaption p,
.streamlit-expanderHeader, .streamlit-expanderHeader *,
.streamlit-expanderContent, .streamlit-expanderContent *,
div[data-testid="stExpander"], div[data-testid="stExpander"] *,
div[data-testid="stText"], div[data-testid="stText"] *,
.stMarkdown, .stMarkdown * {
    color: #2c2c2c !important;
}

/* =============================================
   第三层：重点 → 朱砂红加粗
   （bold/strong，覆盖第二层的深色）
   ============================================= */
strong, b {
    color: #c62828 !important;
    font-weight: bold !important;
    font-size: 1.08em !important;
}

/* =============================================
   第四层：公式 → 竹青绿（最高优先级）
   ============================================= */
.katex, .katex *, .katex .base, .katex .strut,
.katex .mord, .katex .mbin, .katex .mrel,
.katex .mopen, .katex .mclose, .katex .mpunct,
.katex-html, .katex-html * {
    color: #2e7d32 !important;
}

/* =============================================
   第五层：装饰与背景
   ============================================= */
.stApp {
    background: linear-gradient(135deg, #f5f0e1 0%, #ede5d0 50%, #f5f0e1 100%) !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #e8e0cc 0%, #d4c5a9 100%) !important;
    border-right: 2px solid #8b7355 !important;
}

h1, h2, h3 {
    font-family: "STKaiti","KaiTi","楷体","SimSun",serif !important;
}

h1 {
    border-bottom: 3px solid #8b7355;
    padding-bottom: 8px;
}

.stMarkdown, .stTextArea textarea, .stTextInput input {
    font-family: "STKaiti","KaiTi","楷体","SimSun",serif !important;
    line-height: 1.8 !important;
}

.stTextArea textarea, .stTextInput input {
    background: #faf6ed !important;
    border: 1px solid #8b7355 !important;
    border-radius: 6px !important;
}

.stTextArea textarea::placeholder {
    color: #8b7355 !important;
}

.stButton > button, .stFormSubmitButton > button {
    background: #2c2c2c !important;
    color: #f5f0e1 !important;
    border: 1px solid #8b7355 !important;
    border-radius: 6px !important;
    font-family: "STKaiti","KaiTi","楷体",serif !important;
    font-size: 16px !important;
    padding: 8px 28px !important;
    transition: all .2s;
}
.stButton > button:hover {
    background: #4a3728 !important;
    box-shadow: 0 2px 10px rgba(139,115,85,.4) !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: "STKaiti","KaiTi","楷体",serif !important;
    font-size: 18px !important;
}
.stTabs [aria-selected="true"] {
    background: #8b7355 !important;
    color: #f5f0e1 !important;
    border-radius: 4px 4px 0 0 !important;
}

.streamlit-expanderHeader {
    background: #ede5d0 !important;
    border-left: 3px solid #8b7355 !important;
}

hr {
    border: none !important;
    height: 2px !important;
    background: linear-gradient(90deg, transparent, #8b7355, transparent) !important;
}

/* =============================================
   跨课程引导提示框
   ============================================= */
.redirect-box {
    background: linear-gradient(135deg, #fff8e1, #ffecb3);
    border: 2px solid #e65100;
    border-radius: 10px;
    padding: 18px 24px;
    margin: 14px 0;
    font-family: "STKaiti","KaiTi","楷体",serif;
    font-size: 18px;
    color: #3e2723;
    line-height: 2;
}
.redirect-box strong {
    color: #bf360c !important;
}

/* =============================================
   来源文本框（高可读）
   ============================================= */
.source-text-box {
    background: #faf6ed;
    border: 1px solid #8b7355;
    border-radius: 5px;
    padding: 10px 14px;
    color: #2c2c2c;
    font-family: "STKaiti","KaiTi","楷体","SimSun",serif;
    font-size: 14px;
    line-height: 1.7;
    margin: 6px 0;
}
</style>
""", unsafe_allow_html=True)

# ====================== 全局路径 ======================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "index", "images")
CHUNKS_FILE = os.path.join(BASE_DIR, "index", "chunks.jsonl")

EM_KEYWORDS = [
    "电场", "电荷", "电位", "电容", "高斯", "磁场", "导体", "介质",
    "极化", "镜像", "电轴", "偶极", "能量", "电力线", "等位",
    "环路", "散度", "旋度", "梯度", "边界", "矢量", "坐标", "通量",
    "库仑", "安培", "麦克斯韦", "电磁", "传输", "球", "柱", "线",
    "电机", "转矩", "转速", "励磁", "电枢", "变压器", "绕组",
    "感应", "同步", "异步", "直流", "交流", "磁通", "磁链",
]

QA_EXAMPLES = {
    "电磁场": "例：静电场基本方程的微分形式是什么？",
    "电机": "例：异步电动机的转差率是什么？",
}
MK_EXAMPLES = {
    "电磁场": "例：厚度2d的无限大体电荷求电场强度，学生只套了高斯定理没分区域",
    "电机": "例：计算异步电机最大转矩时，学生把转差率当成转速了",
}


# ====================== 工具函数 ======================

def clean_display_text(text):
    if not text:
        return ""
    text = re.sub(
        r"[^\u4e00-\u9fff\w\s.,;:!?()$${}=+\-*/<>≤≥≈∞∇∂∫ΣαβγδεζηθλμπρστφχψωΔΦΩ^_'\"$%&#@~`|\\]",
        " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_em_page(doc_name, page_no):
    if not os.path.exists(CHUNKS_FILE):
        return True
    try:
        with open(CHUNKS_FILE, encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                if c["doc"] == doc_name and c["page"] == page_no:
                    return any(kw in c["text"] for kw in EM_KEYWORDS)
    except Exception:
        pass
    return True


def find_page_images(doc_name, page_no):
    doc_base = os.path.splitext(doc_name)[0]
    pattern = os.path.join(IMG_DIR, f"{doc_base}_p{page_no}_*")
    results = []
    for p in sorted(glob.glob(pattern)):
        try:
            if os.path.getsize(p) < 3000:
                continue
        except Exception:
            continue
        if is_em_page(doc_name, page_no):
            results.append(p)
    return results


def find_imgs_for_section(section_text, sources, max_imgs=2):
    if not sources or len(section_text.strip()) < 15:
        return []
    results = []
    for s in sources:
        if len(results) >= max_imgs:
            break
        source_text = s.get("text", "")
        overlap = sum(1 for kw in EM_KEYWORDS
                       if kw in section_text and kw in source_text)
        if overlap < 2:
            continue
        imgs = find_page_images(s["doc"], s["page"])
        for img_path in imgs[:1]:
            if len(results) < max_imgs:
                cap = f"📖 {s['doc'].replace('.pdf.pdf', '.pdf')} 第{s['page']}页"
                results.append((img_path, cap))
    return results


# ====================== 渲染（公式 + 重点） ======================

def render_formula_block(formula):
    formula = formula.replace("\\vec{", "\\mathbf{")
    formula = formula.replace("\\[8pt]", "\\\\")
    formula = re.sub(r"\\\[|\\\]$$", "", formula)
    formula = formula.replace("$$", "").strip()
    if formula:
        try:
            st.latex(formula)
        except Exception:
            st.code(formula)


def render_text_block(text):
    """渲染文字段落，**bold** 由 CSS 自动变红色"""
    if text.strip():
        st.markdown(text.strip())


def render_answer_with_images(text, sources):
    if not text:
        return
    text = text.replace("\\vec{", "\\mathbf{")
    sections = re.split(r"(^##\s+.+)", text, flags=re.MULTILINE)
    for section in sections:
        if not section.strip():
            continue
        if section.startswith("##"):
            st.markdown(section.strip())
            continue
        parts = re.split(r"(\$\$.+?\$\$)", section, flags=re.DOTALL)
        for part in parts:
            if not part.strip():
                continue
            if part.startswith("$$$$") and part.endswith("$$"):
                render_formula_block(part)
            else:
                render_text_block(part)
        matched = find_imgs_for_section(section.strip(), sources, max_imgs=2)
        if matched:
            cols = st.columns(len(matched))
            for idx, (p, cap) in enumerate(matched):
                cols[idx].image(p, caption=cap, width=300)


def render_redirect_box(redirect_label):
    st.markdown(f"""
    <div class="redirect-box">
        📌 <strong>温馨提示：</strong>您的问题与
        <strong>《{redirect_label}》</strong>
        课程相关，请您移步到
        <strong>【{redirect_label}】</strong>
        答疑模块，可以为您提供更详细的答疑内容。
    </div>
    """, unsafe_allow_html=True)


# ====================== 来源标注（高可读版） ======================

def render_sources(sources, title="来源标注"):
    st.subheader(title)
    if not sources:
        st.markdown(
            '<div class="source-text-box">（综合课程概况回答，非资料片段直接引用）</div>',
            unsafe_allow_html=True)
        return
    for s in sources:
        doc_name = s['doc'].replace('.pdf.pdf', '.pdf')
        with st.expander(
            f"[{s['no']}] {doc_name} "
            f"第{s['page']}页 | 相似度 {s['score']:.3f}"
        ):
            cleaned = clean_display_text(s["text"])
            display_text = cleaned[:300] + ("…" if len(cleaned) > 300 else "")
            safe_text = html_mod.escape(display_text)
            st.markdown(
                f'<div class="source-text-box">{safe_text}</div>',
                unsafe_allow_html=True)
            imgs = find_page_images(s["doc"], s["page"])
            if imgs:
                st.image(imgs[0], width=280)


# ====================== 图片上传 ======================

def image_upload_section(key_prefix, label="上传题目图片"):
    uploaded = st.file_uploader(
        label, type=["png", "jpg", "jpeg", "bmp"],
        key=f"{key_prefix}_upload")
    if uploaded:
        st.image(uploaded, caption="📷 已上传的图片", width=350)
        if st.button("🔍 识别图片中的文字", key=f"{key_prefix}_ocr"):
            with st.spinner("正在识别图片…"):
                text, method = extract_text_from_image(uploaded.getvalue())
            if text:
                st.session_state[f"{key_prefix}_ocr_text"] = text
                st.success(f"✅ 识别成功（{method}）")
                st.text_area("识别结果（可编辑后提交）",
                             value=text, height=120,
                             key=f"{key_prefix}_ocr_result")
            else:
                st.warning(f"⚠️ 识别失败：{method}")
    return st.session_state.get(f"{key_prefix}_ocr_text", "")


# ====================== 页面标题 ======================

st.markdown("""
<div style="text-align:center; padding:18px 0 6px 0;
     background:linear-gradient(180deg,rgba(139,115,85,0.1),transparent);">
    <span style="font-size:2.2em;">🏮</span>
    <span style="font-size:2.6em; font-family:'STKaiti','KaiTi','楷体',serif;
         color:#2c2c2c; letter-spacing:10px; vertical-align:middle;">
        课 程 智 能 答 疑
    </span>
    <span style="font-size:2.2em;">🏮</span>
    <div style="margin-top:4px; color:#5d4037; font-size:0.95em;
         font-family:'STKaiti','KaiTi','楷体',serif; letter-spacing:4px;">
        ─── 墨香学苑 · 答疑解惑 ───
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#5d4037;'>创新点：① 来源溯源  ② 错题解析  ③ 图片识别  ④ 水墨风格</p>",
    unsafe_allow_html=True)

# ====================== Tab ======================

tab1, tab2 = st.tabs(["📖 课程答疑（来源溯源）", "✏️ 错题解析"])

# ---------- Tab1 课程答疑 ----------
with tab1:
    course_choice = st.radio(
        "选择课程",
        options=list(config.COURSES.keys()),
        format_func=lambda k: config.COURSES[k]["label"],
        horizontal=True, key="qa_course")
    course_label = config.COURSES[course_choice]["label"]

    ocr_text = image_upload_section(
        "qa", f"上传{course_label}的题目图片")

    default_text = ocr_text or ""
    example_text = QA_EXAMPLES.get(course_choice, "请输入问题")
    q = st.text_area(
        f"请输入问题（{example_text}）",
        value=default_text, height=80, key="qa_input")

    if st.button("🎯 提问", key="qa_btn"):
        query_text = q.strip() or ocr_text
        if query_text:
            with st.spinner("检索资料并生成回答…"):
                res = answer(query_text, course=course_choice,
                             course_name=course_label)
            st.markdown("---")
            if res.get("redirect"):
                render_redirect_box(res.get("redirect_label", ""))
            else:
                st.subheader("📝 回答")
                render_answer_with_images(res["answer"], res["sources"])
                st.markdown("---")
                render_sources(res["sources"])
        else:
            st.warning("请先输入问题或上传图片。")

# ---------- Tab2 错题解析 ----------
with tab2:
    course_choice2 = st.radio(
        "选择课程",
        options=list(config.COURSES.keys()),
        format_func=lambda k: config.COURSES[k]["label"],
        horizontal=True, key="mk_course")
    course_label2 = config.COURSES[course_choice2]["label"]

    ocr_text2 = image_upload_section(
        "mk", f"上传{course_label2}的错题照片")

    m_example = MK_EXAMPLES.get(course_choice2, "请粘贴错题")
    m = st.text_area(
        f"请粘贴{course_label2}的错题（{m_example}）",
        value=ocr_text2 or "", height=160, key="mk_input")

    if st.button("📝 解析错题", key="mk_btn"):
        mistake_text = m.strip() or ocr_text2
        if mistake_text:
            with st.spinner("检索知识点并生成错题解析…"):
                res = analyze_mistake(
                    mistake_text, course=course_choice2,
                    course_name=course_label2)
            st.markdown("---")
            if res.get("redirect"):
                render_redirect_box(res.get("redirect_label", ""))
            else:
                st.subheader("📋 错题解析报告")
                render_answer_with_images(res["report"], res["sources"])
                st.markdown("---")
                render_sources(res["sources"], title="引用知识点出处")
        else:
            st.warning("请先输入错题或上传图片。")

# ====================== 页脚 ======================
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#5d4037; padding:12px;
     font-family:'STKaiti','KaiTi','楷体',serif; letter-spacing:3px;">
    ───  学而不厌 · 诲人不倦  ───
</div>
""", unsafe_allow_html=True)
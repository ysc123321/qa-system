# -*- coding: utf-8 -*-
"""
资料解析与切分模块 v4：
- 支持 PDF / DOCX / TXT / PPTX
- 自动扫描各课程子文件夹，打课程标签
"""
import os, re, json, glob
import config


# ====================== 读取各类文件 ======================

def read_pdf(path):
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            # 如果文字提不出来（扫描版），尝试OCR
            if not text.strip():
                try:
                    text = ocr_page(page)
                except Exception:
                    pass
            pages.append((i, text))
    return pages


def ocr_page(page):
    """对扫描版PDF页面进行OCR识别（需安装 tesseract + pytesseract + pdf2image）"""
    import pytesseract
    from PIL import Image
    # 将PDF页面渲染为图片
    pil_img = page.to_image(resolution=200).original
    # OCR识别（中文+英文）
    text = pytesseract.image_to_string(pil_img, lang="chi_sim+eng")
    return text.strip()

def read_docx(path):
    import docx
    d = docx.Document(path)
    text = "\n".join(p.text for p in d.paragraphs if p.text.strip())
    return [(1, text)]


def read_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [(1, f.read())]


def read_pptx(path):
    """读取 PPT/PPTX 文件，按幻灯片提取文字"""
    from pptx import Presentation
    prs = Presentation(path)
    slides = []
    for i, slide in enumerate(prs.slides, start=1):
        texts = []
        for shape in slide.shapes:
            # 文本框
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    t = para.text.strip()
                    if t:
                        texts.append(t)
            # 表格
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        t = cell.text.strip()
                        if t:
                            texts.append(t)
        slides.append((i, "\n".join(texts)))
    return slides


# ====================== 文本清洗 ======================

GARBLED_CHARS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd\u25a1\u25a0\u25cb\u25cf\u2610\u2611\u2717\u2718]"
)


def clean_text(text):
    if not text:
        return ""
    text = GARBLED_CHARS.sub("", text)
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"=\s*\n\s*", " = ", text)
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        if len(s) <= 2 and not re.search(r"[\u4e00-\u9fff a-zA-Z0-9]", s):
            continue
        cleaned.append(line)
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ====================== 切分 ======================

def split_chunks(text, page_no, doc_name, course, size, overlap):
    text = clean_text(text)
    if not text:
        return []
    sentences = re.split(r"(?<=[。！？；\n])", text)
    chunks, buf, idx = [], "", 1
    for s in sentences:
        if not s:
            continue
        if len(buf) + len(s) <= size:
            buf += s
        else:
            if buf:
                chunks.append({
                    "doc": doc_name, "page": page_no, "chunk_id": idx,
                    "course": course, "text": buf.strip()
                })
                idx += 1
                buf = buf[-overlap:] + s
            else:
                buf = s
    if buf.strip():
        chunks.append({
            "doc": doc_name, "page": page_no, "chunk_id": idx,
            "course": course, "text": buf.strip()
        })
    return chunks


# ====================== 主入口 ======================

def read_any_file(path):
    """根据扩展名自动选择读取方式（含容错）"""
    ext = os.path.splitext(path)[1].lower()
    name = os.path.basename(path)
    try:
        if ext == ".pdf":
            pages = read_pdf(path)
            if all(not t.strip() for _, t in pages):
                print(f"[警告] {name}: 扫描版PDF，提不出文字，建议用OCR工具转文字版")
                return []
            return pages
        elif ext == ".docx":
            return read_docx(path)
        elif ext == ".pptx":
            return read_pptx(path)
        elif ext == ".ppt":
            print(f"[跳过] {name}: 旧版PPT格式，不支持解析。请用WPS/PowerPoint另存为 .pptx 格式后重新放入")
            return []
        elif ext == ".txt":
            return read_txt(path)
        else:
            print(f"[跳过] {name}: 不支持的文件格式")
            return []
    except Exception as e:
        print(f"[错误] {name}: 解析失败 - {e}")
        return []

def ingest_all():
    os.makedirs(config.INDEX_DIR, exist_ok=True)
    all_chunks = []

    for course_key, course_info in config.COURSES.items():
        course_dir = os.path.join(config.DATA_DIR, course_info["data_subdir"])
        if not os.path.isdir(course_dir):
            print(f"[跳过] 课程目录不存在: {course_dir}")
            continue

        # 扫描所有支持的格式
        files = []
        for ext in ("*.pdf", "*.docx", "*.pptx", "*.ppt", "*.txt"):
            files += glob.glob(os.path.join(course_dir, ext))
        if not files:
            print(f"[跳过] {course_info['label']}: 目录下没有资料文件")
            continue

        course_label = course_info["label"]
        for path in sorted(files):
            name = os.path.basename(path)
            pages = read_any_file(path)
            if not pages:
                continue
            n = 0
            for page_no, text in pages:
                cs = split_chunks(
                    text, page_no, name, course_key,
                    config.CHUNK_SIZE, config.CHUNK_OVERLAP
                )
                all_chunks += cs
                n += len(cs)
            print(f"[解析] [{course_label}] {name}: {len(pages)} 页 -> {n} 个片段")

    out = os.path.join(config.INDEX_DIR, "chunks.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"[完成] 共 {len(all_chunks)} 个片段，已写入 {out}")
    return all_chunks
# -*- coding: utf-8 -*-
"""
从 PDF / PPTX 中提取课件插图
- 自动扫描各课程子文件夹
- 过滤导航按钮等模板元素
- 过滤太小的装饰图
- 只保留课程相关的图片
"""
import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

EM_KEYWORDS = [
    "电场", "电荷", "电位", "电容", "高斯", "磁场", "导体", "介质",
    "极化", "镜像", "电轴", "偶极", "能量", "电力线", "等位",
    "环路", "散度", "旋度", "梯度", "边界", "矢量", "坐标", "通量",
    "库仑", "安培", "麦克斯韦", "电磁", "传输", "球", "柱", "线",
    "电机", "转矩", "转速", "励磁", "电枢", "变压器", "绕组",
    "感应", "同步", "异步", "直流", "交流", "磁通", "磁链",
]


# ====================== PDF 图片提取 ======================

def extract_pdf_images(pdf_path, out_dir):
    import pdfplumber
    name = os.path.splitext(os.path.basename(pdf_path))[0]

    # 第一遍：收集所有图片尺寸和页文本
    size_count = {}
    all_images = []
    page_texts = {}

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            page_texts[i] = text
            for j, img in enumerate(page.images):
                w = int(abs(img["x1"] - img["x0"]))
                h = int(abs(img["bottom"] - img["top"]))
                size_key = (w, h)
                size_count[size_key] = size_count.get(size_key, 0) + 1
                all_images.append((i, j, img, size_key))

    # 检测模板尺寸（导航按钮等在 >30% 页面上重复）
    template_sizes = {
        k for k, v in size_count.items() if v > total_pages * 0.3
    }
    print(f"[检测] {name}: 发现 {len(template_sizes)} 种模板尺寸，将被过滤")

    # 第二遍：提取非模板、课程相关页面的图片
    count = 0
    skipped_template = 0
    skipped_small = 0
    skipped_non_em = 0

    with pdfplumber.open(pdf_path) as pdf:
        for i, j, img, size_key in all_images:
            if size_key in template_sizes:
                skipped_template += 1
                continue
            w, h = size_key
            if w < 120 or h < 40:
                skipped_small += 1
                continue
            if not any(kw in page_texts.get(i, "") for kw in EM_KEYWORDS):
                skipped_non_em += 1
                continue
            try:
                page = pdf.pages[i - 1]
                cropped = page.crop(
                    (img["x0"], img["top"], img["x1"], img["bottom"])
                )
                pil_img = cropped.to_image(resolution=150)
                out_path = os.path.join(out_dir, f"{name}_p{i}_{j}.png")
                pil_img.save(out_path)
                count += 1
            except Exception:
                continue

    print(
        f"[图片] {name}: 提取 {count} 张 | "
        f"过滤模板 {skipped_template} 张，小图 {skipped_small} 张，无关页 {skipped_non_em} 张"
    )


# ====================== PPTX 图片提取 ======================

def extract_pptx_images(pptx_path, out_dir):
    """从 PPTX 中提取嵌入的图片"""
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    name = os.path.splitext(os.path.basename(pptx_path))[0]
    prs = Presentation(pptx_path)
    count = 0
    skipped_small = 0

    for i, slide in enumerate(prs.slides, start=1):
        # 收集该页的文字（用于关键词过滤）
        slide_text = ""
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    slide_text += para.text + " "

        # 如果页面不含课程关键词，跳过（除非页面没有文字）
        has_text = len(slide_text.strip()) > 5
        has_keyword = any(kw in slide_text for kw in EM_KEYWORDS)
        if has_text and not has_keyword:
            continue

        # 提取图片
        for j, shape in enumerate(slide.shapes):
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    image = shape.image
                    # 跳过太小的图标
                    if shape.width < 500000 or shape.height < 500000:  # EMU单位，约<0.5cm
                        skipped_small += 1
                        continue
                    ext = image.ext or "png"
                    out_path = os.path.join(out_dir, f"{name}_p{i}_{j}.{ext}")
                    with open(out_path, "wb") as f:
                        f.write(image.blob)
                    count += 1
                except Exception:
                    continue

    print(
        f"[图片] {name}: 提取 {count} 张 PPT 图片 | "
        f"过滤小图 {skipped_small} 张"
    )


# ====================== 主入口 ======================

def extract_any_file(path, out_dir):
    """根据扩展名自动选择提取方式"""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        extract_pdf_images(path, out_dir)
    elif ext == ".pptx" or ext == ".ppt":
        extract_pptx_images(path, out_dir)
    else:
        pass  # DOCX/TXT 不提图


if __name__ == "__main__":
    out_dir = os.path.join(config.INDEX_DIR, "images")
    os.makedirs(out_dir, exist_ok=True)

    # 清空旧图片
    old = glob.glob(os.path.join(out_dir, "*"))
    for f in old:
        os.remove(f)
    print(f"[清理] 已删除旧图片 {len(old)} 张")

    # 扫描所有课程子文件夹
    total_files = 0
    for course_key, course_info in config.COURSES.items():
        course_dir = os.path.join(config.DATA_DIR, course_info["data_subdir"])
        if not os.path.isdir(course_dir):
            print(f"[跳过] 课程目录不存在: {course_dir}")
            continue

        files = []
        for ext in ("*.pdf", "*.pptx", "*.ppt"):
            files += glob.glob(os.path.join(course_dir, ext))

        if not files:
            print(f"[跳过] {course_info['label']}: 没有可提取图片的文件")
            continue

        print(f"\n===== 处理课程: {course_info['label']} =====")
        for path in sorted(files):
            extract_any_file(path, out_dir)
            total_files += 1

    print(f"\n[完成] 共处理 {total_files} 个文件，图片提取结束")
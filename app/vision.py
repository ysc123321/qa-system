# -*- coding: utf-8 -*-
"""
图片识别模块：从照片/截图中提取题目文字
策略1: DeepSeek 视觉 API（在线，需API支持多模态）
策略2: rapidocr 本地OCR（离线，中文识别好）
策略3: pytesseract 本地OCR（需额外安装 Tesseract-OCR）
"""
import base64
import io
import config


def image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")


def try_deepseek_vision(image_bytes):
    """尝试 DeepSeek 视觉 API"""
    import requests
    b64 = image_to_base64(image_bytes)
    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.DEEPSEEK_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text",
                 "text": "请识别图片中的全部文字内容，包括题目、公式、符号和学生的解题过程。只输出识别到的文字。"},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }],
        "temperature": 0.1,
    }
    r = requests.post(config.DEEPSEEK_API_URL, headers=headers,
                      json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def try_rapidocr(image_bytes):
    """尝试 rapidocr 本地 OCR"""
    from rapidocr_onnxruntime import RapidOCR
    import numpy as np
    from PIL import Image
    ocr = RapidOCR()
    img = Image.open(io.BytesIO(image_bytes))
    result, _ = ocr(np.array(img))
    if result:
        return "\n".join([line[1] for line in result])
    return ""


def try_pytesseract(image_bytes):
    """尝试 pytesseract OCR（需安装 Tesseract-OCR）"""
    import pytesseract
    from PIL import Image
    img = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(img, lang="chi_sim+eng").strip()


def extract_text_from_image(image_bytes):
    """
    多策略提取图片文字。
    返回 (识别文本, 方法名) 或 (None, 错误摘要)
    """
    strategies = [
        ("DeepSeek视觉", try_deepseek_vision),
        ("rapidocr本地OCR", try_rapidocr),
        ("pytesseract", try_pytesseract),
    ]
    errors = []
    for name, func in strategies:
        try:
            text = func(image_bytes)
            if text and len(text.strip()) > 3:
                return text, name
            errors.append(f"{name}:结果为空")
        except ImportError:
            errors.append(f"{name}:未安装")
        except Exception as e:
            errors.append(f"{name}:{str(e)[:40]}")
    return None, "; ".join(errors)
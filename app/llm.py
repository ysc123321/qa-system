# -*- coding: utf-8 -*-
"""大模型调用模块：DeepSeek（OpenAI 兼容接口）"""
import requests
import config


def chat(messages, temperature=0.2):
    headers = {"Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
               "Content-Type": "application/json"}
    payload = {"model": config.DEEPSEEK_MODEL, "messages": messages,
               "temperature": temperature, "stream": False}
    r = requests.post(config.DEEPSEEK_API_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
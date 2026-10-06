# -*- coding: utf-8 -*-
"""一键入库：解析 → 切分 → 向量化 → 保存索引"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.ingest import ingest_all
from app.vector_store import TfidfStore

if __name__ == "__main__":
    chunks = ingest_all()
    store = TfidfStore()
    store.build(chunks)
    store.save()
    print("[完成] 入库结束，可运行 python main.py 提问")
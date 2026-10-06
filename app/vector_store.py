# -*- coding: utf-8 -*-
"""向量化入库与检索 v3：支持按课程过滤"""
import os, json, joblib, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import config


class TfidfStore:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self.matrix = None
        self.chunks = []

    def build(self, chunks):
        self.chunks = chunks
        self.matrix = self.vectorizer.fit_transform([c["text"] for c in chunks])
        print(f"[入库] 向量矩阵维度: {self.matrix.shape}")

    def save(self, index_dir=None):
        index_dir = index_dir or config.INDEX_DIR
        os.makedirs(index_dir, exist_ok=True)
        joblib.dump(self.vectorizer, os.path.join(index_dir, "tfidf_vectorizer.pkl"))
        joblib.dump(self.matrix, os.path.join(index_dir, "tfidf_matrix.pkl"))
        with open(os.path.join(index_dir, "chunks.jsonl"), "w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, index_dir=None):
        index_dir = index_dir or config.INDEX_DIR
        s = cls()
        s.vectorizer = joblib.load(os.path.join(index_dir, "tfidf_vectorizer.pkl"))
        s.matrix = joblib.load(os.path.join(index_dir, "tfidf_matrix.pkl"))
        with open(os.path.join(index_dir, "chunks.jsonl"), encoding="utf-8") as f:
            s.chunks = [json.loads(line) for line in f if line.strip()]
        return s

    def search(self, query, top_k=None, course=None):
        """检索：可按课程过滤（course=None 表示全部课程）"""
        top_k = top_k or config.TOP_K
        q = self.vectorizer.transform([query])
        sims = cosine_similarity(q, self.matrix)[0]

        # 按课程过滤
        if course:
            mask = np.array([
                c.get("course", "") == course for c in self.chunks
            ])
            sims = np.where(mask, sims, 0)  # 非本课程的相似度置零

        order = np.argsort(sims)[::-1][:top_k]
        return [
            {"score": float(sims[i]), **self.chunks[i]}
            for i in order if sims[i] > 0
        ]
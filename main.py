# -*- coding: utf-8 -*-
"""控制台入口：python main.py （exit 退出）"""
from app.qa import answer

if __name__ == "__main__":
    print("=== 《工程电磁场》答疑系统（控制台版） ===")
    while True:
        q = input("\n学生提问 > ").strip()
        if not q or q.lower() in ("exit", "quit", "q"):
            break
        res = answer(q)
        print("\n【回答】\n" + res["answer"])
        print("\n【来源片段】")
        for s in res["sources"]:
            print(f"[{s['no']}] {s['doc']} 第{s['page']}页 (相似度 {s['score']:.3f})")
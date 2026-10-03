#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 knowledge_base/data/*.json 内嵌进 上岸花园v2.html 的 KB:DATA 标记区。
运行: python3 build_kb_embed.py
每日自动化更新后需重新运行本脚本，知识库才会出现在前端。
"""
import os, re, json

BASE = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(BASE, "data")
HTML = os.path.join(BASE, "..", "garden_build", "上岸花园v2.html")

def load(name, default):
    p = os.path.join(DATA, name)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print("读取失败", p, e)
    return default

kb = {
    "affairs": load("current_affairs.json", {"items": []}),
    "essay": load("essay.json", {"real_topics": [], "materials": []}),
    "categories": load("categories.json", {"categories": []}),
    "shenlun_tools": load("shenlun_tools.json", {"standard_words": [], "golden_words": [], "guwen": [], "templates": [], "cases": []}),
    "study_plan": load("study_plan.json", {"stages": [], "weekly_template": [], "milestones": [], "diagnosis": []}),
}

payload = "window.KB_DATA=" + json.dumps(kb, ensure_ascii=False) + ";"
src = open(HTML, encoding="utf-8").read()
pat = re.compile(r"(<!--KB:DATA:START-->).*?(<!--KB:DATA:END-->)", re.S)
if not pat.search(src):
    raise SystemExit("HTML 中未找到 KB:DATA 标记区")
new = pat.sub(lambda m: m.group(1) + "\n<script>" + payload + "</script>\n" + m.group(2), src)
open(HTML, "w", encoding="utf-8").write(new)
a = len(kb["affairs"].get("items", []))
e = len(kb["essay"].get("real_topics", [])) + len(kb["essay"].get("materials", []))
c = len(kb["categories"].get("categories", []))
s = len(kb["shenlun_tools"].get("standard_words", []))
print("已内嵌：时政 %d 条 / 申论 %d 条 / 分类 %d 大类 / 申论工具 %d 领域 -> %s" % (a, e, c, s, HTML))

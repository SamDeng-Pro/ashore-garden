#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建「申论写作工具三件套」结构化数据 + 扩充申论范文深度剖析。

数据源（申论教练「粉笔·小申」专家的题库，CC 许可开源）：
  - 规范词库：8 大领域 160+ 规范词（大白话->规范表达）
  - 金词库：238 个高频金词（词-场景-真题）
  - 金句库：五大领域主题 + 通用金句模板 + 高频案例 + 古文引用

输出 data/shenlun_tools.json，供 build_kb_embed.py 内嵌前端。
"""
import os, re, json, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
# 申论语料源目录（CC 许可开源数据），可用环境变量覆盖；默认数据已构建进 data/shenlun_tools.json
REF = os.environ.get("GARDEN_SHENLUN_REF", os.path.join(BASE, "..", "raw", "shenlun-ref"))
DATA = os.path.join(BASE, "..", "data")
OUT = os.path.join(DATA, "shenlun_tools.json")

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

# ---------- 1. 规范词库（申论规范词库.md）----------
def parse_standard_words():
    txt = read(os.path.join(REF, "shenlun-standard-words/references/申论规范词库.md"))
    # 按 "## 一、社会治理" 等章节切分
    domains = []
    # 章节标题形如 ## 一、社会治理 / ## 二、经济发展 ...
    sections = re.split(r"\n## ", txt)
    for sec in sections[1:]:
        # sec 首行是 "一、社会治理"
        lines = sec.split("\n")
        title_line = lines[0].strip()
        m = re.match(r"[一二三四五六七八九十]+、(.+)", title_line)
        if not m:
            continue
        name = m.group(1).strip()
        words = []
        # 表格行：| 词 | 场景 |
        for ln in lines:
            if not ln.strip().startswith("|"):
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] and cells[0] not in ("规范词汇", "---", "应用场景"):
                words.append({"word": cells[0], "scene": cells[1] if len(cells) > 1 else ""})
        if words:
            domains.append({"domain": name, "words": words})
    return domains

# ---------- 2. 金词库（金词索引.md 提取词名清单）----------
def parse_golden_words():
    txt = read(os.path.join(REF, "shenlun-word-accumulate/references/金词索引.md"))
    # 提取各主题词清单（"### 主题（N 词）" 后的行）
    themes = []
    sections = re.split(r"\n### ", txt)
    for sec in sections[1:]:
        lines = sec.split("\n")
        title = lines[0].strip()
        m = re.match(r"(.+?)（(\d+) 词）", title)
        if not m:
            continue
        theme = m.group(1).strip()
        # 词清单在标题后的段落（可能换行），词形如 "私搭乱建(33)、..."
        body = "\n".join(lines[1:])
        body = body.split("## ")[0]  # 去掉后续章节
        # 提取所有 "词(数字)" 或 "词" 形式
        words = re.findall(r"([\u4e00-\u9fa5A-Za-z0-9“”·（）\-]+?)\(\d+\)", body)
        words = [w for w in words if w and len(w) <= 12 and not w.startswith("###")]
        # 去重保序
        seen, uniq = set(), []
        for w in words:
            if w not in seen:
                seen.add(w); uniq.append(w)
        if uniq:
            themes.append({"theme": theme, "words": uniq})
    return themes

# ---------- 3. 金句库（申论主题分类与金句库.md）----------
def parse_quotes():
    txt = read(os.path.join(REF, "shenlun-quote-expander/references/申论主题分类与金句库.md"))
    # 古文引用：标题含"类"且表格表头含"出处"（古文/出处/适用场景）
    guwen = []
    sections = re.split(r"\n### ", txt)
    for sec in sections[1:]:
        lines = sec.split("\n")
        title = lines[0].strip()
        if not re.search(r"类$", title):
            continue
        if "出处" not in sec:
            continue
        for ln in lines:
            if not ln.strip().startswith("|"):
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[0] and not cells[0].startswith("-") and cells[0] not in ("古文",):
                guwen.append({"quote": cells[0], "source": cells[1], "scene": cells[2]})
    # 通用金句模板（"### 开头点题型" 等，含 "型"）
    templates = []
    for sec in sections[1:]:
        lines = sec.split("\n")
        title = lines[0].strip()
        if "型" not in title:
            continue
        items = []
        for ln in lines:
            ln = ln.strip()
            if ln.startswith("- ") and "XX" in ln:
                items.append(ln[2:].strip("「」"))
        if items:
            templates.append({"type": title, "items": items})
    # 案例库：标题含"类"且表头含"事迹要点"
    cases = []
    for sec in sections[1:]:
        lines = sec.split("\n")
        title = lines[0].strip()
        if "类" not in title:
            continue
        if "事迹要点" not in sec:
            continue
        for ln in lines:
            if not ln.strip().startswith("|"):
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[0] and not cells[0].startswith("-") and cells[0] not in ("案例",):
                cases.append({"name": cells[0], "desc": cells[1], "tags": cells[2]})
    return guwen, templates, cases

def main():
    std_words = parse_standard_words()
    golden = parse_golden_words()
    guwen, templates, cases = parse_quotes()

    payload = {
        "meta": {
            "title": "申论写作工具三件套（规范词/金词/金句）",
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "粉笔·公考申论教练（开源题库）",
            "source_url": "https://github.com/WangJunqing-coder/shenlun-skill",
            "rule": "规范词/金词/金句均为公开教学素材，客观中立",
        },
        "standard_words": std_words,
        "golden_words": golden,
        "guwen": guwen,
        "templates": templates,
        "cases": cases,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    n_std = sum(len(d["words"]) for d in std_words)
    n_gold = sum(len(t["words"]) for t in golden)
    print(f"规范词 {len(std_words)} 领域 / {n_std} 词")
    print(f"金词 {len(golden)} 主题 / {n_gold} 词")
    print(f"古文 {len(guwen)} 条 / 模板 {len(templates)} 类 / 案例 {len(cases)} 条")
    print(f"-> {OUT}")

if __name__ == "__main__":
    main()

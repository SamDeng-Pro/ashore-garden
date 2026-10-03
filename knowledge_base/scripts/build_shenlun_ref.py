#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 shenlun_ref/*.md（开源申论名师方法论）解析成结构化的申论素材 JSON，
注入 essay.json 的 materials 数组（作为「方法论/素材库」板块）。
运行: python3 build_shenlun_ref.py
"""
import os, re, json

BASE = os.path.join(os.path.dirname(__file__), "..")
REF = os.path.join(BASE, "shenlun_ref")
ESSAY = os.path.join(BASE, "data", "essay.json")

def read(name):
    p = os.path.join(REF, name + ".md")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    return ""

# 金句素材库：按主题拆成结构化条目
def parse_jinju(text):
    """从 jinju-sucai.md 提取八大主题的金句、案例、分论点模板"""
    themes = []
    # 按「## 一、」这类二级标题切块
    blocks = re.split(r"\n##\s+[一二三四五六七八九十]+、", text)
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        # 主题名 = 第一行
        lines = b.split("\n")
        title = re.sub(r"[#\s]", "", lines[0]).strip()
        # 提取金句（数字列表）
        quotes = []
        cases = []
        points = []
        cur = None
        for ln in lines:
            ln = ln.strip()
            if ln.startswith("###") and "金句" in ln:
                cur = "quotes"; continue
            if ln.startswith("###") and "案例" in ln:
                cur = "cases"; continue
            if ln.startswith("###") and "分论点" in ln:
                cur = "points"; continue
            if ln.startswith("##") or ln.startswith("---"):
                cur = None; continue
            if cur == "quotes":
                m = re.match(r"^\d+\.\s*(.+)$", ln)
                if m and len(m.group(1)) > 2:
                    quotes.append(m.group(1))
            elif cur == "cases":
                # 表格行 | 案例 | 内容 | 主题 |
                cells = [c.strip() for c in ln.strip("|").split("|")]
                if len(cells) >= 2 and cells[0] and not cells[0].startswith("--") and "案例" not in cells[0]:
                    cases.append({"name": cells[0], "desc": cells[1] if len(cells) > 1 else "", "theme": cells[2] if len(cells) > 2 else ""})
            elif cur == "points":
                m = re.match(r"^[-*]\s*分论点\d+[:：]\s*(.+)$", ln)
                if m:
                    points.append(m.group(1))
        if title and (quotes or cases or points):
            themes.append({"theme": title, "quotes": quotes, "cases": cases, "points": points})
    return themes

# 真题六步解析：从 zhenti-shili.md 提取例题
def parse_zhenti(text):
    examples = []
    blocks = re.split(r"\n###\s+", text)
    for b in blocks:
        b = b.strip()
        if not b or b.startswith("#"):
            continue
        lines = b.split("\n")
        title = lines[0].strip() if lines else ""
        # 找「题目」「材料」「解析」等段落
        ti = b.find("**题目**")
        ma = b.find("**材料**")
        ana = b.find("**解析**")
        topic = ""
        if ti >= 0:
            end = b.find("\n", ti)
            topic = b[ti+len("**题目**"):end if end>0 else len(b)].strip().lstrip("：:")
        material = ""
        if ma >= 0:
            end = b.find("\n\n", ma)
            if end < 0: end = len(b)
            material = b[ma+len("**材料**"):end].strip().lstrip("：:").replace("> ", "").replace(">", "")
        analysis = ""
        if ana >= 0:
            analysis = b[ana+len("**解析**"):].strip().lstrip("：:")
        if topic or analysis:
            examples.append({"title": title, "question": topic, "material": material, "analysis": analysis})
    return examples

def parse_guifan(text):
    """规范表达：提取动宾结构表达"""
    items = []
    for ln in text.split("\n"):
        ln = ln.strip()
        m = re.match(r"^[-*]\s*(.+)$", ln)
        if m:
            s = m.group(1)
            # 只保留「A→B」或「A：B」或「A——B」形式的对照
            if "→" in s or "：" in s or "——" in s:
                items.append(s)
    return items

jinju = parse_jinju(read("jinju-sucai"))
zhenti = parse_zhenti(read("zhenti-shili"))
guifan = parse_guifan(read("guifan-biaoda"))

# 组装进 essay.json 的 materials（追加「方法论」类型素材，不动已有素材）
essay = json.load(open(ESSAY, encoding="utf-8"))
materials = essay.get("materials", [])

# 1. 金句素材库 → 一个「申论金句素材库（八大主题）」素材条目（含子结构）
if jinju:
    materials.append({
        "title": "申论金句与素材库（八大主题）",
        "date": "2026-10-02",
        "type": "金句素材库",
        "gist": "按八大主题（经济/乡村/民生/生态/文化/科技/治理/人物）分类汇总的金句、案例、分论点模板，附大作文开头结尾三式模板。",
        "full_text": "八大主题金句、案例、分论点模板详见下方结构分析。",
        "structure": "八大主题 → 每主题含[金句/案例/分论点模板] → 附人物素材与大作文开头结尾模板",
        "points": [t["theme"] + "：" + "；".join(t["quotes"][:3]) for t in jinju if t.get("quotes")],
        "golden_sentences": [q for t in jinju for q in (t.get("quotes") or [])][:20],
        "usage": "大作文论据库。写分论点时直接套用各主题的「分论点模板」，论证时引用对应主题金句+案例。",
        "source_media": "申论名师公开教学精华（开源整理）",
        "source_url": "https://github.com/WangJunqing-coder/shenlun-skill",
        "_themes": jinju
    })

# 2. 真题六步解析 → 每条例题一个素材
for ex in zhenti[:12]:
    materials.append({
        "title": ex["title"] or "申论真题示例",
        "date": "2026-10-02",
        "type": "真题解析",
        "gist": ex["question"][:60] if ex.get("question") else "六步解析示例",
        "full_text": (ex.get("material") or "")[:500],
        "structure": "题型识别 → 审题 → 找点 → 加工 → 书写 → 易错点",
        "points": [],
        "golden_sentences": [],
        "usage": (ex.get("analysis") or "").strip(),
        "source_media": "申论名师公开教学精华（开源整理）",
        "source_url": "https://github.com/WangJunqing-coder/shenlun-skill",
        "_question": ex.get("question", ""),
        "_analysis": ex.get("analysis", "")
    })

# 3. 规范表达 → 一个素材条目
if guifan:
    materials.append({
        "title": "申论规范表达（书面语对照）",
        "date": "2026-10-02",
        "type": "规范表达",
        "gist": "口语化表达与规范书面语对照，提升申论作答的专业度。",
        "full_text": "常见口语化表达与规范表达对照。",
        "structure": "口语化 → 规范表达",
        "points": guifan[:30],
        "golden_sentences": [],
        "usage": "作答时把口语替换为规范表达，避免大白话，体现机关文风。",
        "source_media": "申论名师公开教学精华（开源整理）",
        "source_url": "https://github.com/WangJunqing-coder/shenlun-skill"
    })

essay["materials"] = materials
essay["meta"]["updated_at"] = "2026-10-02"
json.dump(essay, open(ESSAY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("申论素材已增强：金句主题 %d 组 / 真题解析 %d 条 / 规范表达 %d 条 / 素材总数 %d" % (
    len(jinju), len(zhenti[:12]), len(guifan), len(materials)))

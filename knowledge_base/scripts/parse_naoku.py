#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把「考公脑库」真题笔记解析成前端 JSON。
输入: raw/naoku_src/10-真题/<模块>/<大类>/*.md
输出: data/questions_index.json（全量索引）、data/questions_seed.json（前端内嵌精选）
优化: 单次遍历 + 复用正则 + 只读必要字段，避免慢。
"""
import os, re, json

BASE = os.path.dirname(__file__)
REPO = os.path.normpath(os.path.join(BASE, "..", "raw", "naoku_src"))
DIR_Q = os.path.join(REPO, "10-真题")
OUT_IDX = os.path.normpath(os.path.join(BASE, "..", "data", "questions_index.json"))
OUT_SEED = os.path.normpath(os.path.join(BASE, "..", "data", "questions_seed.json"))

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
KV_RE = re.compile(r"^\s*([^:#]+?)\s*:\s*(.*?)\s*$")
IMG_RE = re.compile(r"!\[\[[^\]]*\]\]")
LINK_RE = re.compile(r"\[\[([^\]|]*\|)?([^\]]+)\]\]")
TAG_RE = re.compile(r"<[^>]+>")

def parse_fm(text):
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        kv = KV_RE.match(line)
        if kv:
            fm[kv.group(1).strip()] = kv.group(2).strip().strip('"')
    return fm, text[m.end():]

def clean(s):
    s = IMG_RE.sub("[图]", s)
    s = LINK_RE.sub(lambda m: m.group(2), s)
    s = TAG_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def main():
    if not os.path.isdir(DIR_Q):
        print("目录不存在:", DIR_Q); return
    items = []
    for module in os.listdir(DIR_Q):
        mdir = os.path.join(DIR_Q, module)
        if not os.path.isdir(mdir): continue
        for cat in os.listdir(mdir):
            cdir = os.path.join(mdir, cat)
            if not os.path.isdir(cdir): continue
            try:
                files = [f for f in os.listdir(cdir) if f.endswith(".md")]
            except Exception:
                continue
            for fn in files:
                p = os.path.join(cdir, fn)
                try:
                    text = open(p, encoding="utf-8").read()
                except Exception:
                    continue
                fm, body = parse_fm(text)
                # 用标题切段，只取需要的段落
                stem = reason = fast = trap = mother = ""
                for sec_title, sec_body in re.findall(r"^#{1,4}\s*(.+?)\s*$(.*?)(?=^#{1,4}\s|\Z)", body, re.S | re.M):
                    t = sec_title.strip()
                    b = clean(sec_body)[:400]
                    if "推理链" in t and not reason: reason = b
                    elif ("易错" in t or "陷阱" in t) and not trap: trap = b
                    elif "母题" in t and not mother: mother = b
                    elif "最快" in t and not fast: fast = b
                    elif t == "题干" and not stem: stem = b
                # 最快解法也常出现在**最快解法**行内，用行匹配兜底
                if not fast:
                    mm = re.search(r"\*\*最快解法\*\*[：:]\s*(.{0,200})", body)
                    if mm: fast = clean(mm.group(1))[:300]
                items.append({
                    "id": "%s-%s-%s" % (module, cat, fn[:-3]),
                    "module": module, "category": cat,
                    "year": fm.get("年份", ""), "region": fm.get("地区", ""),
                    "paper": fm.get("试卷", ""), "title": fn[:-3],
                    "stem": stem[:300], "reasoning": reason, "fast": fast,
                    "trap": trap, "mother": mother,
                    "source": "github.com/ERRRC/kaogongzhentizhengliu"
                })
    # 写全量索引
    json.dump({"meta": {"count": len(items),
                        "source": "考公脑库 github.com/ERRRC/kaogongzhentizhengliu (2016-2026)",
                        "modules": ["资料分析", "判断推理"]},
               "items": items},
              open(OUT_IDX, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("索引完成:", len(items), "->", OUT_IDX)

    # 前端精选：近5年(2022-2026)，每模块每大类抽最多8题
    groups = {}
    for it in items:
        try: y = int(it["year"])
        except Exception: y = 0
        if y < 2022: continue
        groups.setdefault((it["module"], it["category"]), []).append(it)
    seed = []
    for key in sorted(groups):
        arr = sorted(groups[key], key=lambda x: x["year"], reverse=True)
        seed.extend(arr[:8])
    json.dump({"meta": {"count": len(seed), "rule": "2022-2026 每模块每大类至多8题",
                        "source": "考公脑库 github.com/ERRRC/kaogongzhentizhengliu"},
               "items": seed},
              open(OUT_SEED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("精选完成:", len(seed), "->", OUT_SEED)

if __name__ == "__main__":
    main()

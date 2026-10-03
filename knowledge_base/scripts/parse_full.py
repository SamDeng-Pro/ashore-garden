#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把「考公脑库」真题笔记解析成含完整选项+答案的前端 JSON。
输入: raw/naoku_src/10-真题/<模块>/<大类>/*.md
输出: data/questions_full.json（全量，含 options/answer）
      data/questions_seed.json（前端内嵌精选，近5年每类限量）

相比 parse_naoku.py 的关键改进：
1. 提取完整选项 A/B/C/D 及正确答案（识别选项后的 ✅ 标记）
2. 提取官方解析（完整版，而非截断的推理链）
3. 只保留纯文字题（跳过含 <img> 公式图/题目图的题）
"""
import os, re, json

BASE = os.path.dirname(__file__)
REPO = os.path.normpath(os.path.join(BASE, "..", "raw", "naoku_src"))
DIR_Q = os.path.join(REPO, "10-真题")
OUT_FULL = os.path.normpath(os.path.join(BASE, "..", "data", "questions_full.json"))
OUT_SEED = os.path.normpath(os.path.join(BASE, "..", "data", "questions_seed.json"))

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
KV_RE = re.compile(r"^\s*([^:#]+?)\s*:\s*(.*?)\s*$")
LINK_RE = re.compile(r"\[\[([^\]|]*\|)?([^\]]+)\]\]")
IMG_RE = re.compile(r"<img[^>]*>")
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
    s = IMG_RE.sub("", s)            # 去掉公式/题目图片标签
    s = LINK_RE.sub(lambda m: m.group(2), s)
    s = TAG_RE.sub("", s)
    s = s.replace("\u200b", "").replace("　", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()

def split_sections(body):
    """用 ### 标题切分段落，返回 {标题: 正文}"""
    parts = re.split(r"(?m)^#{1,4}\s*(.+?)\s*$", body)
    # parts[0] 是首个标题前的空文本
    sec = {}
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i+1] if i+1 < len(parts) else ""
        sec[title] = content
    return sec

def parse_options(opt_text):
    """从选项文本解析 A/B/C/D 和正确答案"""
    options = {}
    answer = None
    # 按 "A." / "B." 等切分（支持中文点号）
    lines = re.split(r"(?m)^\s*[-*]?\s*([A-D])\s*[\.、．:：]\s*", opt_text)
    # lines[0] 是第一个选项前的空文本
    for i in range(1, len(lines), 2):
        letter = lines[i]
        content = lines[i+1] if i+1 < len(lines) else ""
        content = clean(content)
        is_correct = "✅" in content or "✔" in content
        content = content.replace("✅", "").replace("✔", "").strip()
        options[letter] = content
        if is_correct and answer is None:
            answer = letter
    return options, answer

def main():
    if not os.path.isdir(DIR_Q):
        print("目录不存在:", DIR_Q); return
    items = []
    skipped_img = 0
    for module in sorted(os.listdir(DIR_Q)):
        mdir = os.path.join(DIR_Q, module)
        if not os.path.isdir(mdir):
            continue
        for cat in sorted(os.listdir(mdir)):
            cdir = os.path.join(mdir, cat)
            if not os.path.isdir(cdir):
                continue
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
                sec = split_sections(body)

                stem_raw = sec.get("题干", "")
                opt_raw = sec.get("选项", "")
                off_raw = sec.get("官方解析", sec.get("解析", ""))
                reason_raw = sec.get("推理链", "")
                trap_raw = sec.get("易错点", sec.get("陷阱", ""))
                mother_raw = sec.get("母题抽象", sec.get("母题", ""))

                # 判定是否含图片：任一关键段落含 <img 则跳过
                joined = "".join([stem_raw, opt_raw, off_raw, reason_raw, mother_raw])
                if "<img" in joined or "formula-" in joined:
                    skipped_img += 1
                    continue

                stem = clean(stem_raw)
                options, answer = parse_options(opt_raw)
                official = clean(off_raw)
                reason = clean(reason_raw)
                trap = clean(trap_raw)
                mother = clean(mother_raw)

                # 最快解法可能在推理链里，也可能独立成行
                fast = ""
                mm = re.search(r"\*\*最快解法\*\*[：:]\s*(.{0,200})", body)
                if mm:
                    fast = clean(mm.group(1))[:300]

                # 若选项里没识别到 ✅，从官方解析里推断答案
                if answer is None and official:
                    am = re.search(r"正确答案为\s*([A-D])", official)
                    if am:
                        answer = am.group(1)

                items.append({
                    "id": "%s-%s-%s" % (module, cat, fn[:-3]),
                    "module": module, "category": cat,
                    "year": fm.get("年份", ""), "region": fm.get("地区", ""),
                    "paper": fm.get("试卷", ""), "title": fn[:-3],
                    "stem": stem, "options": options, "answer": answer,
                    "official": official, "reasoning": reason,
                    "fast": fast, "trap": trap, "mother": mother,
                    "source": "github.com/ERRRC/kaogongzhentizhengliu"
                })

    json.dump({"meta": {"count": len(items),
                        "source": "考公脑库 github.com/ERRRC/kaogongzhentizhengliu (2016-2026)",
                        "modules": ["资料分析", "判断推理"],
                        "note": "仅纯文字题，已剔除含公式/图形图片的题"},
               "items": items},
              open(OUT_FULL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("全量完成:", len(items), "题，跳过含图题:", skipped_img, "->", OUT_FULL)

    # 前端精选：近5年(2022-2026)，每模块每大类抽最多10题
    groups = {}
    for it in items:
        try:
            y = int(it["year"])
        except Exception:
            y = 0
        if y < 2022:
            continue
        groups.setdefault((it["module"], it["category"]), []).append(it)
    seed = []
    for key in sorted(groups):
        arr = sorted(groups[key], key=lambda x: x["year"], reverse=True)
        seed.extend(arr[:10])
    json.dump({"meta": {"count": len(seed),
                        "rule": "2022-2026 每模块每大类至多10题（纯文字题）",
                        "source": "考公脑库 github.com/ERRRC/kaogongzhentizhengliu"},
               "items": seed},
              open(OUT_SEED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("精选完成:", len(seed), "->", OUT_SEED)

if __name__ == "__main__":
    main()

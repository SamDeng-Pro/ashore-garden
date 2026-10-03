#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时政数据整合：把 crawl_affairs.py 抓取的原文，整合成前端可用的结构化数据。

输出 data/current_affairs.json：
  每条 = 标题 + 正文原文 + 来源 + 日期 + 考点分类（客观）+ 记忆要点（客观）

设计原则：
  - 「考点分类」是客观归类（属于政治理论/科技/法律等哪类）
  - 「记忆要点」是客观的事实性要点提炼（时间/地点/名称/数字），不做价值判断
  - 绝不编造事实，全部来自爬取的原文
"""
import os, json, re, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
RAW = os.path.join(DATA, "current_affairs_raw.json")
OUT = os.path.join(DATA, "current_affairs.json")

# 关键词 -> 考点分类（客观归类规则）
CATEGORY_RULES = [
    ("政治理论", ["总书记", "习近平", "全会", "党中央", "中国共产党", "现代化", "改革", "治国理政"]),
    ("科技航天", ["火箭", "卫星", "航天", "嫦娥", "空间站", "发射", "北斗", "科技", "创新"]),
    ("经济民生", ["经济", "消费", "制造业", "产业", "就业", "收入", "民生", "市场"]),
    ("国际外交", ["国际", "外交", "金砖", "东盟", "联合国", "峰会", "合作", "全球"]),
    ("法律政策", ["法律", "条例", "法规", "政策", "意见", "办法", "制度", "规定"]),
    ("文化教育", ["文化", "教育", "非遗", "文物", "历史", "高校", "人才"]),
    ("生态绿色", ["生态", "环保", "绿色", "碳", "能源", "气候", "长江", "黄河"]),
]

def classify(title, body):
    text = (title or "") + (body or "")
    for cat, kws in CATEGORY_RULES:
        for kw in kws:
            if kw in text:
                return cat
    return "综合"

def extract_facts(title, body):
    """客观事实要点：提取含数字、时间、地点的句子片段"""
    facts = []
    # 提取含年份/数字的句子
    sentences = re.split(r"[。；！？]", body)
    for s in sentences:
        if re.search(r"\d", s) and len(s) < 80:
            s = s.strip()
            if s and s not in facts:
                facts.append(s)
        if len(facts) >= 3:
            break
    return facts

def main():
    raw = json.load(open(RAW, encoding="utf-8"))
    items = raw.get("items", [])

    out_items = []
    for it in items:
        if not it.get("body"):
            continue
        cat = classify(it["title"], it["body"])
        facts = extract_facts(it["title"], it["body"])
        out_items.append({
            "date": it["date"],
            "title": it["title"],
            "source_media": it["source"],
            "source_url": it["url"],
            "page": it.get("page", ""),
            "category": cat,           # 客观归类
            "full_text": it["body"],   # 原文
            "facts": facts,            # 客观事实要点
            "summary": it["body"][:120] + ("…" if len(it["body"]) > 120 else ""),
        })

    # 按日期倒序
    out_items.sort(key=lambda x: x["date"], reverse=True)

    payload = {
        "meta": {
            "title": "时政热点库（考公向 · 含原文）",
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "update_cycle": "daily",
            "rule": "原文来自权威媒体，客观中立；考点分类为客观归类，记忆要点为事实提炼，均不带价值倾向",
            "authoritative_sources": ["人民日报", "新华社", "央视新闻", "求是", "经济日报"],
        },
        "items": out_items,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"时政整合完成：{len(out_items)} 条 -> {OUT}")


if __name__ == "__main__":
    main()

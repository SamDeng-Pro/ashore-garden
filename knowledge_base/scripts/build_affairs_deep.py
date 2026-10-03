#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时政数据增强（重写版）：
  1. 过滤噪音：责编署名、过短内容（<100字，多为图片说明）
  2. 按 title 去重（人民日报同一文章跨版面导读重复）
  3. 修复 full_text 重复 bug（整篇正文被贴两遍）
  4. 补充「深度解析」字段（考点解读 + 申论角度 + 行测角度）
  5. 精细化分类（与 categories.json 时事政治二级考点对齐）

深度解析原则：客观、中立，只做「考点提示 + 学习角度」，不做价值判断、不编造事实。
"""
import os, re, json, datetime
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
RAW = os.path.join(DATA, "current_affairs_raw.json")
OUT = os.path.join(DATA, "current_affairs.json")

# 噪音过滤关键词
NOISE_TITLE = ["责编", "本版", "版面"]
MIN_BODY_LEN = 100  # 短于这个长度视为图片说明/导读，过滤

def dedupe_full_text(body):
    """去除爬虫重复粘贴的正文（整篇文章被贴了两遍）"""
    if not body:
        return body
    lines = body.split("\n")
    n = len(lines)
    if n < 6:
        return body
    first = lines[0].strip()
    if not first:
        return body
    dup_start = None
    for i in range(1, n):
        if lines[i].strip() == first:
            match_cnt = 0
            for j in range(i, min(n, i + 3)):
                if lines[j].strip() == lines[j - i].strip():
                    match_cnt += 1
            if match_cnt >= 2:
                dup_start = i
                break
    if dup_start:
        return "\n".join(lines[:dup_start]).strip()
    return body

def classify(title, body):
    """精细化分类：标题优先，正文辅助。返回时政二级考点名（对齐 categories.json sz_*）"""
    t = (title or "")
    text = t + " " + (body or "")[:300]
    # 国际外交（标题信号最强）
    if any(k in t for k in ["国际", "外交", "金砖", "东盟", "联合国", "峰会", "多国", "命运共同体", "对华", "大使", "合作", "外长"]):
        return "国际外交"
    # 科技航天
    if any(k in t for k in ["火箭", "卫星", "航天", "嫦娥", "空间站", "发射", "北斗", "量子", "数智", "数字", "智能", "5G", "AI", "科技", "创新", "动能", "展会"]):
        return "科技航天"
    # 民生社会
    if any(k in t for k in ["民生", "就业", "收入", "养老", "医疗", "教育", "消费", "市场", "品牌", "服务", "流动", "出行", "体育", "射击", "奥运", "经贸", "香港", "澳门"]):
        return "民生社会"
    # 政策文件
    if any(k in t for k in ["条例", "法规", "办法", "规定", "政策", "意见", "制度", "改革", "方案", "规划", "一见", "评论", "随笔", "短评", "社论"]):
        return "政策文件"
    # 文化传承/精神（长征、红色、精神、复兴、文化）—— 归入重要会议/讲话（精神谱系属政治类）
    if any(k in t for k in ["长征", "红色", "精神", "复兴", "文化", "非遗", "文物", "历史", "赓续"]):
        return "重要会议/讲话"
    # 重要会议/讲话（国庆、现代化、强国、总书记、习近平、升旗）
    if any(k in t for k in ["国庆", "现代化", "强国", "总书记", "习近平", "升旗", "华诞", "招待会", "讲话", "党代会", "全会"]):
        return "重要会议/讲话"
    # 兜底：正文辅助判断
    if any(k in text for k in ["总书记", "习近平", "现代化", "强国"]):
        return "重要会议/讲话"
    if any(k in text for k in ["国际", "外交", "合作", "全球"]):
        return "国际外交"
    if any(k in text for k in ["科技", "创新", "数字", "智能"]):
        return "科技航天"
    if any(k in text for k in ["民生", "就业", "消费", "市场"]):
        return "民生社会"
    return "重要会议/讲话"

def deep_analysis(cat, title, body):
    text = (title or "") + (body or "")[:600]
    angle = []
    if any(k in text for k in ["总书记", "习近平", "党中央", "中国共产党", "招待会", "讲话", "现代化", "强国"]):
        angle.append({
            "考点": "重要会议/领导人讲话",
            "解读": "时政高频考点，重点记忆讲话中的核心论断、重大判断与标志性表述，常以常识判断或申论材料背景形式出现。",
            "申论角度": "讲话精神可作为申论大作文的立意来源与论据引用，如「中国式现代化」「以人民为中心」等主题。",
            "行测角度": "常识判断常考讲话中的新提法、新表述；政治理论模块可能考查讲话出处与核心要义。"
        })
    if any(k in text for k in ["火箭", "卫星", "航天", "嫦娥", "空间站", "发射", "北斗", "量子", "数智", "数字化", "智能", "科技", "创新", "动能"]):
        angle.append({
            "考点": "科技航天/数字经济",
            "解读": "科技成就与数字经济是常识判断高频考点，重点记忆成就名称、时间节点、首次/突破等关键信息。",
            "申论角度": "科技创新素材，可支撑「科技自立自强」「新质生产力」「数字中国」等大作文主题。",
            "行测角度": "常识判断考成就与意义对应；注意「首次」「突破」等限定词。"
        })
    if any(k in text for k in ["经济", "消费", "制造", "产业", "就业", "收入", "民生", "市场", "展会", "品牌", "养老", "医疗", "教育"]):
        angle.append({
            "考点": "经济民生",
            "解读": "民生经济类政策是申论与行测双高频，重点把握政策的目标、举措与成效。",
            "申论角度": "民生保障、高质量发展主题的核心论据，可提炼「问题—举措—成效」论证链。",
            "行测角度": "常识判断可能考政策名称、出台背景与具体数字。"
        })
    if any(k in text for k in ["国际", "外交", "金砖", "东盟", "联合国", "峰会", "多国", "命运共同体", "合作", "全球"]):
        angle.append({
            "考点": "国际外交",
            "解读": "外交外事类时政重点记忆主场外交、多边机制、合作倡议的名称与成果。",
            "申论角度": "「人类命运共同体」「对外开放」等主题的宏观背景素材。",
            "行测角度": "常识判断考外交成果与倡议名称对应。"
        })
    if any(k in text for k in ["文化", "非遗", "文物", "历史", "红色", "精神", "长征", "复兴", "博物馆", "传统"]):
        angle.append({
            "考点": "文化传承/精神谱系",
            "解读": "文化类时政是申论文化自信主题的素材富矿，重点把握精神内涵与传承路径。",
            "申论角度": "「文化自信」「精神谱系」「守正创新」等主题的核心案例。",
            "行测角度": "常识判断考精神谱系内涵、红色遗址等。"
        })
    if not angle:
        angle.append({
            "考点": "综合时政",
            "解读": "综合类时政，建议结合具体内容做常识性了解。",
            "申论角度": "可作背景知识储备，理解国家发展大势。",
            "行测角度": "常识判断可能以细节题形式考查。"
        })
    return angle[:2]

def extract_facts(body):
    """客观事实要点：提取含数字/时间/地点的句子片段"""
    facts = []
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
    seen_titles = set()

    for it in items:
        title = (it.get("title") or "").strip()
        body = it.get("body", "") or ""
        # 过滤噪音
        if not title or any(k in title for k in NOISE_TITLE):
            continue
        if len(body) < MIN_BODY_LEN:
            continue
        # 按 title 去重
        if title in seen_titles:
            continue
        seen_titles.add(title)
        # 修 full_text
        full = dedupe_full_text(body)
        cat = classify(title, full)
        out_items.append({
            "date": it.get("date", ""),
            "title": title,
            "source_media": it.get("source", "人民日报"),
            "source_url": it.get("url", ""),
            "page": it.get("page", ""),
            "category": cat,
            "full_text": full,
            "facts": extract_facts(full),
            "summary": full[:120] + ("…" if len(full) > 120 else ""),
            "analysis": deep_analysis(cat, title, full),
        })

    out_items.sort(key=lambda x: x["date"], reverse=True)
    payload = {
        "meta": {
            "title": "时政热点库（考公向 · 含原文 + 深度解析）",
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "update_cycle": "daily",
            "rule": "原文来自权威媒体，客观中立；考点分类为客观归类；深度解析为考点提示与学习角度（客观中立）",
            "authoritative_sources": ["人民日报", "新华社", "央视新闻", "求是", "经济日报"],
        },
        "items": out_items,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"时政增强完成：原始 {len(items)} 条 -> 清洗后 {len(out_items)} 条")
    c = Counter(it["category"] for it in out_items)
    for k, v in c.most_common():
        print(f"  {k}: {v} 条")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考公时政爬虫 —— 从权威媒体抓取时政要闻，结构化存储。

数据源（仅权威媒体，确保真实准确）：
  1. 人民日报电子版（要闻版 01-04 版）: paper.people.com.cn
  2. 新华网要闻: www.xinhuanet.com（备用源）

设计原则：
  - 只抓事实（标题 + 正文 + 时间 + 来源），不做主观评价
  - 增量去重：按 content_id/url 去重，避免重复抓取
  - 结构化输出到 data/current_affairs_raw.json（供后续写解析/考点标注）

用法：
  python crawl_affairs.py            # 抓取今天
  python crawl_affairs.py 20261002   # 抓取指定日期（YYYYMMDD）
"""
import os, sys, re, json, hashlib
import datetime
import requests
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "..", "data")
RAW_FILE = os.path.join(DATA_DIR, "current_affairs_raw.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

RMRB_HOST = "http://paper.people.com.cn/rmrb"
# 只抓这些版面（要闻、评论、理论等对考公有价值的版面）
RMRB_TARGET_PAGES = {"第01版", "第02版", "第03版", "第04版"}


def get(url, timeout=15):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def parse_date(datestr):
    """YYYYMMDD -> date"""
    return datetime.datetime.strptime(datestr, "%Y%m%d").date()


def crawl_rmrb(date):
    """抓取人民日报电子版指定日期的要闻"""
    items = []
    ymd = date.strftime("%Y%m")
    day = date.strftime("%d")
    path = date.strftime("%Y%m/%d")

    # 1. 版面列表
    layout_url = f"{RMRB_HOST}/pc/layout/index.html"
    try:
        html = get(layout_url)
    except Exception as e:
        print(f"[rmrb] 版面列表抓取失败: {e}")
        return items

    soup = BeautifulSoup(html, "lxml")
    node_links = {}
    for a in soup.find_all("a"):
        href = a.get("href", "")
        txt = a.get_text(strip=True)
        if "node_" in href and txt:
            # 只抓目标版面
            for page in RMRB_TARGET_PAGES:
                if page in txt:
                    node_links[href] = txt
                    break

    if not node_links:
        print("[rmrb] 未找到要闻版面")
        return items

    # 2. 逐版抓文章列表
    base_dir = f"{RMRB_HOST}/pc/layout/{path}"
    for node, page_name in node_links.items():
        # node 链接形如 202610/02/node_01.html，相对 layout/ 目录
        node_url = base_dir + "/" + node.split("/")[-1]
        try:
            node_html = get(node_url)
        except Exception as e:
            print(f"[rmrb] 版面 {page_name} 抓取失败: {e}")
            continue

        ns = BeautifulSoup(node_html, "lxml")
        seen_titles = set()
        for a in ns.find_all("a"):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if "content_" not in href or not title:
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)
            # 相对路径 -> 绝对
            content_id = re.search(r"content_(\d+)\.html", href)
            if not content_id:
                continue
            cid = content_id.group(1)
            abs_url = f"{RMRB_HOST}/pc/content/{path}/content_{cid}.html"
            items.append({
                "source": "人民日报",
                "date": date.strftime("%Y-%m-%d"),
                "page": page_name,
                "title": title,
                "url": abs_url,
                "content_id": "rmrb_" + cid,
            })

    # 3. 抓正文（限前 N 篇，避免过载）
    max_articles = 40
    for it in items[:max_articles]:
        try:
            ch = get(it["url"])
        except Exception:
            it["body"] = ""
            continue
        cs = BeautifulSoup(ch, "lxml")
        # 人民日报正文在 <p> 标签里（article-box 内）
        box = cs.find("div", class_="article-box")
        scope = box if box else cs
        paras = [p.get_text(" ", strip=True) for p in scope.find_all("p")]
        it["body"] = "\n".join(p for p in paras if p)
    return items


def dedupe(items):
    """按 content_id 去重（保留已有）"""
    if os.path.exists(RAW_FILE):
        try:
            old = json.load(open(RAW_FILE, encoding="utf-8"))
            old_items = old.get("items", [])
        except Exception:
            old_items = []
    else:
        old_items = []

    existing_ids = {it["content_id"] for it in old_items}
    new_items = [it for it in items if it["content_id"] not in existing_ids]
    merged = old_items + new_items
    return merged, new_items


def save(merged):
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "meta": {
            "title": "时政要闻原文库（权威媒体）",
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": ["人民日报", "新华网"],
            "rule": "仅事实原文，客观中立；解析与考点标注见 current_affairs.json",
        },
        "items": merged,
    }
    with open(RAW_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) > 1:
        date = parse_date(sys.argv[1])
    else:
        date = datetime.date.today()

    print(f"=== 抓取时政要闻 {date} ===")
    items = crawl_rmrb(date)
    print(f"人民日报抓取到 {len(items)} 篇")

    merged, new_items = dedupe(items)
    save(merged)
    print(f"新增 {len(new_items)} 篇，累计 {len(merged)} 篇")
    print(f"已保存到 {RAW_FILE}")


if __name__ == "__main__":
    main()

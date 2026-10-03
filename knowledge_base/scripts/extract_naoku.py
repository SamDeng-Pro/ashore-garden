#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解压考公脑库ZIP（GBK文件名），按中央目录顺序流式提取文本笔记目录，跳过90-图片。"""
import zipfile, os

RAW = os.path.join(os.path.dirname(__file__), "..", "raw")
ZP = os.path.join(RAW, "naoku.zip")
DST = os.path.join(RAW, "naoku_src")

WANT_DIRS = ("10-真题/", "20-考点/", "15-材料/")
WANT_FILES = ("00-使用说明.md", "README.md", "LICENSE")

def dec(name):
    try:
        return name.encode("cp437").decode("gbk")
    except Exception:
        return name

z = zipfile.ZipFile(ZP)
got = 0
for info in z.infolist():          # 顺序遍历，避免随机访问
    full = dec(info.filename)
    if "/" not in full:
        continue
    rel = full.split("/", 1)[1]
    if info.is_dir():
        if any(rel.startswith(w) for w in WANT_DIRS):
            os.makedirs(os.path.join(DST, rel), exist_ok=True)
        continue
    if not (any(rel.startswith(w) for w in WANT_DIRS) or rel in WANT_FILES):
        continue
    target = os.path.join(DST, rel)
    d = os.path.dirname(target)
    if d:
        os.makedirs(d, exist_ok=True)
    with z.open(info) as src, open(target, "wb") as out:
        while True:
            chunk = src.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
    got += 1
    if got % 3000 == 0:
        print("已解压", got, flush=True)
print("解压完成:", got, "->", DST)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日一键更新（自动化专用入口）：
  1. crawl_affairs.py   爬当日人民日报要闻（增量去重）
  2. build_affairs_deep.py  清洗+深度解析+分类（新版，替代 build_affairs.py）
  3. build_shenlun_full.py  申论工具（幂等，快速）
  4. build_kb_embed.py  注入前端 HTML
之后的前端上传发布由 Agent 在自动化会话里执行（edit-flow），脚本只做到本地产物为止。

用法: python3 daily_update.py [YYYYMMDD]
"""
import os, sys, subprocess, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
# 优先用 GARDEN_PYTHON 环境变量指定的解释器（需含 requests/bs4/lxml）；否则用当前 python3
PY = os.environ.get("GARDEN_PYTHON") or sys.executable

STEPS = [
    ("爬取时政", "crawl_affairs.py"),
    ("时政清洗+深度解析", "build_affairs_deep.py"),
    ("申论工具刷新", "build_shenlun_full.py"),
    ("注入前端", "build_kb_embed.py"),
]

def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"=== 每日更新 {datetime.date.today()} ===")
    for name, script in STEPS:
        cmd = [PY, os.path.join(BASE, script)]
        if script == "crawl_affairs.py" and date_arg:
            cmd.append(date_arg)
        print(f"--- {name}: {script} ---")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        out = (r.stdout or "").strip()
        if out:
            print(out[-500:])
        if r.returncode != 0:
            print(f"[失败] {script}: {(r.stderr or '')[-300:]}")
            sys.exit(1)
    print("=== 本地更新完成，待上传发布 ===")

if __name__ == "__main__":
    main()

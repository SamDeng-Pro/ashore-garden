#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全年备考排期数据：从规划师产出转化为前端可用的结构化数据。
输出 data/study_plan.json，由 build_kb_embed.py 注入前端「计划」板块。
"""
import os, json, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
OUT = os.path.join(DATA, "study_plan.json")

payload = {
    "meta": {
        "title": "全年备考排期（研趣规划师 · 2026-10-02 制定）",
        "updated_at": "2026-10-02",
        "review_cycle": "每2周复盘滚动调整",
        "rule": "目标线为渐进式参考值，基于当前真实做题基线制定，达成情况以打卡数据为准",
    },
    "exams": [
        {"name": "国考（练兵）", "date": "2026-11-29"},
        {"name": "省考（决战）", "date": "2027-03-20"},
    ],
    "diagnosis": [
        {"mod": "判断推理", "acc": 89, "note": "优势，保持手感", "level": "good"},
        {"mod": "言语理解", "acc": 68, "note": "题量最大，篇章阅读57%偏弱", "level": "mid"},
        {"mod": "资料分析", "acc": 65, "note": "性价比最高，值得加练", "level": "mid"},
        {"mod": "数量关系", "acc": 60, "note": "保基础题，放弃难题", "level": "weak"},
        {"mod": "常识判断", "acc": 47, "note": "碎片积累", "level": "weak"},
        {"mod": "政治理论", "acc": 40, "note": "最薄弱，与时政申论捆绑补", "level": "weak"},
    ],
    "stages": [
        {
            "name": "补弱筑基期",
            "range": "10/02 - 11/24",
            "goal": "申论8篇；政治理论40%→60%；资料分析65%→75%",
            "weeks": [
                {"w": "W1", "date": "10/5-10/11", "topic": "申论启动：概括归纳", "detail": "周日/周一各1.5h写+对照范文；工作日每天30min政治理论+时政"},
                {"w": "W2", "date": "10/12-10/18", "topic": "申论：综合分析", "detail": "同节奏；周六加1组资料分析限时练"},
                {"w": "W3", "date": "10/19-10/25", "topic": "申论：提出对策", "detail": "数量只刷基础题型（工程/行程/利润）"},
                {"w": "W4", "date": "10/26-11/1", "topic": "申论：贯彻执行（公文）", "detail": "11/1 第一次全真模考（行测）"},
                {"w": "W5", "date": "11/2-11/8", "topic": "申论：大作文框架", "detail": "每周1篇大作文；时政每日15min"},
                {"w": "W6", "date": "11/9-11/15", "topic": "国考真题套卷周", "detail": "隔天1套国考真题（120min限时），错题当日复盘"},
                {"w": "W7", "date": "11/16-11/22", "topic": "模考冲刺周", "detail": "2套全真模考+错题回顾；申论1篇保持手感"},
                {"w": "W8", "date": "11/23-11/28", "topic": "减量缓冲周", "detail": "只做轻量复盘+错题本，考前3天不学新内容"},
            ],
        },
        {
            "name": "复盘调整期",
            "range": "11/30 - 12/27",
            "goal": "国考全面复盘；申论累计14篇；三大件稳75%+",
            "weeks": [
                {"w": "W9", "date": "11/30-12/6", "topic": "国考复盘周", "detail": "逐题分析，输出「我的失分清单」"},
                {"w": "W10", "date": "12/7-12/13", "topic": "失分清单专项修补①", "detail": "申论2篇（1小题+1大作文）"},
                {"w": "W11", "date": "12/14-12/20", "topic": "失分清单专项修补②", "detail": "12月中旬第二次全真模考"},
                {"w": "W12", "date": "12/21-12/27", "topic": "阶段收口", "detail": "对照目标线复盘，调整省考阶段计划"},
            ],
        },
        {
            "name": "省考冲刺期",
            "range": "2027/1/4 - 3/20",
            "goal": "模考稳定达标；申论20+篇；3月中旬进入应试状态",
            "weeks": [
                {"w": "W13-16", "date": "1月", "topic": "专项强化", "detail": "薄弱考点逐个击破；时政开始背年度汇总"},
                {"w": "W17-20", "date": "2月", "topic": "套卷月", "detail": "每周2套省考真题+1篇申论完整卷（180min全真）"},
                {"w": "W21-22", "date": "3月上旬", "topic": "冲刺模考", "detail": "隔天模考，调生物钟到考试时段"},
                {"w": "缓冲", "date": "3/14-3/19", "topic": "减量缓冲周", "detail": "只看错题本和金句，睡够，考前不学新内容"},
            ],
        },
    ],
    "weekly_template": [
        {"day": "周日", "type": "main", "plan": "申论1.5h + 薄弱模块1h", "hours": "2.5h"},
        {"day": "周一", "type": "main", "plan": "套卷/模考或专项", "hours": "2h"},
        {"day": "周二", "type": "light", "plan": "时政/常识碎片", "hours": "0.5h"},
        {"day": "周三", "type": "light", "plan": "资料分析1组(20题)", "hours": "0.5-1h"},
        {"day": "周四", "type": "light", "plan": "政治理论+复盘", "hours": "0.5h"},
        {"day": "周五", "type": "buffer", "plan": "固定buffer/休息（单周下午空可加申论1h）", "hours": "0-1h"},
        {"day": "周六", "type": "light", "plan": "言语/判断保持手感", "hours": "1h"},
    ],
    "milestones": [
        {"date": "11/24", "essay": "8篇", "zzll": "≥60%", "zlfx": "≥75%", "flowers": "3朵"},
        {"date": "12/27", "essay": "14篇", "zzll": "≥65%", "zlfx": "≥78%", "flowers": "5朵"},
        {"date": "2027/2底", "essay": "20篇", "zzll": "≥70%", "zlfx": "≥80%", "flowers": "8朵"},
        {"date": "3/20", "essay": "22篇+", "zzll": "≥70%", "zlfx": "≥80%", "flowers": "全花园盛放"},
    ],
    "review": "每2周周日晚看数据页复盘；模考后输出失分清单；偏离时砍次要保主线（申论+资料+政治理论）",
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print("排期数据已生成 ->", OUT)
print("阶段:", len(payload["stages"]), "| 周计划:", sum(len(s["weeks"]) for s in payload["stages"]), "| 里程碑:", len(payload["milestones"]))

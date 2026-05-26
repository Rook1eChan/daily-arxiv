#!/usr/bin/env python3
"""arXiv cs.CL 每日论文抓取、翻译、打标签、生成网页"""

import argparse
import json
import os
import sys

from fetch_papers import fetch_today_papers, fetch_papers_by_date
from translate import translate_papers
from generate_html import build_html
from generate_index import generate_main_index


def date_to_dirname(date_str):
    parts = date_str.replace(",", "").split()
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
    }
    if len(parts) == 1 and "-" in date_str:
        return date_str
    if len(parts) >= 3:
        day = parts[1].zfill(2)
        month = month_map.get(parts[2], "00")
        year = parts[3]
        return f"{year}-{month}-{day}"
    return date_str


def main():
    parser = argparse.ArgumentParser(description="arXiv cs.CL 每日论文抓取")
    parser.add_argument("--date", help="指定日期 (YYYY-MM-DD)，如 2026-05-22")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 50)
    if args.date:
        print(f"Step 1: 获取 {args.date} 的 cs.CL 论文...")
        date_str, papers = fetch_papers_by_date(args.date)
    else:
        print("Step 1: 抓取 arXiv cs.CL 今日论文...")
        date_str, papers = fetch_today_papers()

    if not papers:
        print("未能获取论文（arXiv 周末不更新或指定日期无新投稿）")
        return

    date_dir = date_to_dirname(date_str if date_str else args.date or "")
    output_dir = os.path.join(base_dir, "output", date_dir)

    print(f"  日期: {date_str}")
    print(f"  论文数量: {len(papers)} 篇")
    print(f"  输出目录: output/{date_dir}/")

    print("=" * 50)
    print("Step 2: 翻译标题和摘要...")
    papers, token_usage = translate_papers(papers)

    print("=" * 50)
    print("Step 3: 打标签（翻译时已完成）...")

    for tag in ["agent-benchmark", "agent-memory", "agentic-rl"]:
        count = sum(1 for p in papers if tag in p.get("tags", []))
        print(f"  {tag}: {count} 篇")

    pt = token_usage["prompt_tokens"]
    ct = token_usage["completion_tokens"]
    tt = token_usage["total_tokens"]
    print(f"\n  Token 消耗: prompt={pt}, completion={ct}, total={tt}")
    print(f"  模型: qwen-flash (免费)")

    os.makedirs(output_dir, exist_ok=True)
    token_file = os.path.join(output_dir, "token_usage.txt")
    if not os.path.exists(token_file):
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(f"prompt_tokens: {pt}\ncompletion_tokens: {ct}\ntotal_tokens: {tt}\n")
    data_file = os.path.join(output_dir, "papers.json")
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"  数据已保存: {data_file}")

    print("=" * 50)
    print("Step 4: 生成 HTML 页面...")
    build_html(papers, date_str or args.date or "", output_dir)

    print("=" * 50)
    print("Step 5: 刷新主页面...")
    generate_main_index(base_dir)

    print("=" * 50)
    print("全部完成!")


if __name__ == "__main__":
    main()

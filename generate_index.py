import json
import os


def scan_output(output_dir):
    entries = []
    if not os.path.exists(output_dir):
        return entries

    for name in sorted(os.listdir(output_dir), reverse=True):
        date_dir = os.path.join(output_dir, name)
        if not os.path.isdir(date_dir) or name == ".ipynb_checkpoints":
            continue
        data_file = os.path.join(date_dir, "papers.json")
        html_file = os.path.join(date_dir, "index.html")
        if not os.path.exists(html_file):
            continue

        papers = []
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    papers = json.load(f)
            except Exception:
                papers = []

        tags = {}
        for p in papers:
            for t in p.get("tags", []):
                tags[t] = tags.get(t, 0) + 1

        entries.append({
            "date": name,
            "total": len(papers),
            "tags": tags,
        })

    return entries


def build_index(entries, output_dir):
    rows = ""
    for e in entries:
        tag_badges = ""
        for t in ["agent-benchmark", "agent-memory", "agentic-rl"]:
            cnt = e["tags"].get(t, 0)
            if cnt > 0:
                tag_badges += f'<span class="badge">{t}: {cnt}</span>'

        label = e["date"]
        link = f"{e['date']}/index.html"
        rows += f"""
        <tr>
            <td><a href="{link}">{label}</a></td>
            <td>{e["total"]}</td>
            <td>{tag_badges}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily arXiv - 总览</title>
<style>
:root {{ --bg: #f8fafc; --card: #ffffff; --text: #1e293b; --sec: #64748b; --border: #e2e8f0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; line-height: 1.6; }}
.container {{ max-width: 800px; margin: 0 auto; }}
.header {{ text-align: center; padding: 30px 0; border-bottom: 2px solid var(--border); margin-bottom: 30px; }}
.header h1 {{ margin: 0; font-size: 1.8em; }}
.header .subtitle {{ color: var(--sec); margin-top: 8px; }}
.section {{ margin: 30px 0; }}
.section h2 {{ font-size: 1.2em; margin-bottom: 12px; }}
.manual-box {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 30px; }}
.manual-box code {{ background: #f1f5f9; padding: 2px 8px; border-radius: 4px; font-size: 0.9em; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ text-align: left; padding: 12px 16px; border-bottom: 1px solid var(--border); }}
th {{ font-weight: 600; color: var(--sec); font-size: 0.85em; text-transform: uppercase; }}
tr:hover td {{ background: #f1f5f9; }}
a {{ color: #2563eb; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.badge {{ display: inline-block; font-size: 0.75em; padding: 2px 8px; border-radius: 10px; background: #e2e8f0; color: #475569; margin: 1px 3px; }}
.footer {{ text-align: center; padding: 30px 0; color: var(--sec); font-size: 0.85em; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📄 Daily arXiv</h1>
        <div class="subtitle">自动抓取 + AI 翻译 + 领域打标 · 共 {len(entries)} 天</div>
    </div>

    <div class="section">
        <h2>🔍 获取指定日期的论文</h2>
        <div class="manual-box">
            <p>在 GitHub 仓库手动触发 Workflow，填写日期即可：</p>
            <ol>
                <li>打开 <a href="https://github.com/Rook1eChan/daily-arxiv/actions" target="_blank">Actions 页面</a></li>
                <li>选择 <strong>Daily arXiv Paper</strong> → 点击 <strong>Run workflow</strong></li>
                <li>在 <strong>date</strong> 输入框填入日期，格式 <code>YYYY-MM-DD</code>（如 <code>2026-05-22</code>）</li>
                <li>点击 <strong>Run workflow</strong>，等待完成</li>
            </ol>
        </div>
    </div>

    <div class="section">
        <h2>📚 历史论文列表</h2>
        <table>
            <thead>
                <tr><th>日期</th><th>论文数</th><th>标签</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>

    <div class="footer">
        <a href="https://github.com/Rook1eChan/daily-arxiv" target="_blank">GitHub 仓库</a>
        · 数据来源: <a href="https://arxiv.org/list/cs.CL/recent" target="_blank">arXiv cs.CL</a>
        · 翻译: 阿里百炼 Qwen
    </div>
</div>
</body>
</html>"""

    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"主页面已生成: {output_path}")


def generate_main_index(root_dir):
    output_dir = os.path.join(root_dir, "output")
    entries = scan_output(output_dir)
    build_index(entries, output_dir)

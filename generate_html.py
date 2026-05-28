import os


def build_html(papers, date_label, output_dir):
    tagged = [p for p in papers if p.get("tags")]
    untagged = [p for p in papers if not p.get("tags")]

    tag_groups = {}
    for p in tagged:
        for t in p["tags"]:
            tag_groups.setdefault(t, []).append(p)

    tag_colors = {
        "agent-benchmark": "#3b82f6",
        "agent-memory": "#8b5cf6",
        "agentic-rl": "#ef4444",
    }
    tag_emojis = {
        "agent-benchmark": "📊",
        "agent-memory": "🧠",
        "agentic-rl": "🤖",
    }

    def paper_card(p):
        tags_html = ""
        for t in p.get("tags", []):
            color = tag_colors.get(t, "#6b7280")
            tags_html += f'<span class="tag" style="background:{color}20;color:{color};border:1px solid {color}40">{t}</span>'

        title_cn = p.get("title_translated", "") or ""
        summary_cn = p.get("summary_translated", "") or ""
        title_en = p["title"]
        summary_en = p["summary"]
        authors = ", ".join(p["authors"][:5])
        if len(p["authors"]) > 5:
            authors += " et al."

        t_diff = f'<div class="title-cn">{title_cn}</div>' if title_cn else ""
        s_diff = ""
        if summary_cn:
            s_diff = f'<details><summary>中文翻译</summary><div class="summary-cn">{summary_cn}</div></details>'

        return f"""
        <div class="paper">
            <div class="paper-header">
                <span class="arxiv-id">[{p["arxiv_id"]}]</span>
                <div class="paper-tags">{tags_html}</div>
            </div>
            <div class="title-en">{title_en}</div>
            {t_diff}
            <div class="summary-en">{summary_en}</div>
            {s_diff}
            <div class="meta">
                <span class="authors">👤 {authors}</span>
                <span class="date">📅 {p.get("published_date", "")}</span>
                <a class="link" href="https://arxiv.org/abs/{p["arxiv_id"]}" target="_blank">🔗 arXiv</a>
            </div>
        </div>"""

    tagged_sections = ""
    for tag in ["agent-benchmark", "agent-memory", "agentic-rl"]:
        tag_papers = tag_groups.get(tag, [])
        if not tag_papers:
            continue
        color = tag_colors.get(tag, "#6b7280")
        emoji = tag_emojis.get(tag, "🏷️")
        cards = "".join(paper_card(p) for p in tag_papers)
        tagged_sections += f"""
        <h2 class="section-title" id="{tag}" style="border-left:4px solid {color};padding-left:12px">
            {emoji} {tag} <span class="count">({len(tag_papers)}篇)</span>
        </h2>
        <div class="paper-list">{cards}</div>"""

    all_cards = "".join(paper_card(p) for p in untagged)

    tag_nav = ""
    for tag in ["agent-benchmark", "agent-memory", "agentic-rl"]:
        count = len(tag_groups.get(tag, []))
        if count > 0:
            color = tag_colors.get(tag, "#6b7280")
            emoji = tag_emojis.get(tag, "🏷️")
            tag_nav += f'<a href="#{tag}" style="background:{color}20;color:{color}">{emoji} {tag} ({count})</a>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily arXiv - {date_label}</title>
<style>
:root {{ --bg: #f8fafc; --card-bg: #ffffff; --text: #1e293b; --text-secondary: #64748b; --border: #e2e8f0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; line-height: 1.6; }}
.container {{ max-width: 960px; margin: 0 auto; }}
.header {{ text-align: center; padding: 30px 0; border-bottom: 2px solid var(--border); margin-bottom: 30px; }}
.header h1 {{ margin: 0; font-size: 1.8em; }}
.header .subtitle {{ color: var(--text-secondary); margin-top: 8px; }}
.nav {{ display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin: 20px 0; }}
.nav a {{ padding: 8px 16px; border-radius: 20px; text-decoration: none; font-size: 0.9em; font-weight: 500; transition: all .2s; }}
.nav a:hover {{ transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
.section-title {{ font-size: 1.3em; margin: 30px 0 15px; display: flex; align-items: center; gap: 8px; }}
.section-title .count {{ font-size: 0.7em; color: var(--text-secondary); font-weight: 400; }}
.paper-list {{ display: flex; flex-direction: column; gap: 16px; }}
.paper {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; transition: box-shadow .2s; }}
.paper:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,.06); }}
.paper-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.arxiv-id {{ font-family: monospace; font-size: 0.85em; color: var(--text-secondary); }}
.paper-tags {{ display: flex; gap: 6px; }}
.tag {{ font-size: 0.75em; padding: 2px 10px; border-radius: 12px; font-weight: 500; }}
.title-en {{ font-size: 1.05em; font-weight: 600; margin-bottom: 6px; }}
.title-cn {{ font-size: 0.95em; color: #2563eb; margin-bottom: 8px; }}
.summary-en {{ font-size: 0.9em; color: var(--text-secondary); margin-bottom: 8px; }}
details {{ margin-bottom: 8px; }}
details summary {{ font-size: 0.85em; color: #2563eb; cursor: pointer; user-select: none; }}
.summary-cn {{ font-size: 0.9em; color: #475569; margin-top: 6px; padding: 10px; background: #f1f5f9; border-radius: 8px; }}
.meta {{ display: flex; gap: 16px; font-size: 0.85em; color: var(--text-secondary); flex-wrap: wrap; }}
.meta .link {{ color: #2563eb; text-decoration: none; }}
.meta .link:hover {{ text-decoration: underline; }}
.footer {{ text-align: center; padding: 30px 0; color: var(--text-secondary); font-size: 0.85em; }}
@media (max-width: 640px) {{ body {{ padding: 10px; }} .paper {{ padding: 14px; }} }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📄 Daily arXiv</h1>
        <div class="subtitle">{date_label} · 共 {len(papers)} 篇</div>
        <div class="nav">
            <a href="#all" style="background:#e2e8f0;color:#1e293b">📋 全部 ({len(papers)})</a>
            {tag_nav}
        </div>
    </div>

    {tagged_sections}

    <h2 class="section-title" id="all">📋 全部论文 <span class="count">({len(papers)}篇)</span></h2>
    <div class="paper-list">{all_cards}</div>

    <div class="footer">
        由自动脚本抓取 · 数据来源: <a href="https://arxiv.org/list/cs.CL/recent" target="_blank">arXiv cs.CL</a> · 翻译: 阿里百炼 Qwen · <a href="https://github.com/Rook1eChan/daily-arxiv" target="_blank">GitHub</a>
    </div>
</div>
</body>
</html>"""

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "index.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML 页面已生成: {output_file}")

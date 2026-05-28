# Daily arXiv

每天自动抓取 [arXiv cs.CL](https://arxiv.org/list/cs.CL/recent) 最新论文，翻译标题和摘要，对 agent 相关领域打标签，生成网页方便浏览。

## 功能

- 每日自动抓取（北京时间 10:00）
- 阿里百炼 Qwen 翻译标题+摘要 → 中文
- LLM 自动分类三个领域：
  - `agent-benchmark` — 智能体基准测试/评估
  - `agent-memory` — 智能体记忆/记忆增强
  - `agentic-rl` — 智能体强化学习
- 按日期归档，保留历史数据
- GitHub Pages 在线浏览

## 手动获取指定日期

在 [Actions 页面](https://github.com/Rook1eChan/daily-arxiv/actions) 点击 **Run workflow**，填写日期 `YYYY-MM-DD`（如 `2026-05-22`）即可。

## 本地运行

```bash
pip install -r requirements.txt
export DASHSCOPE_API_KEY="your-api-key"
python main.py              # 今天
python main.py --date 2026-05-22  # 指定日期
```

## 输出结构

```
output/
├── index.html              # 主页面（所有日期列表）
├── 2026-05-25/
│   ├── index.html          # 当日论文
│   └── papers.json         # 数据（含翻译、标签）
└── ...
```

## 扩展到其他领域

系统设计支持轻松扩展到其他 arXiv 分类：

**更换类别**（如 `cs.LG`、`cs.AI`、`cs.CV`、`cs.RO`）：
- 改 URL 中的 `cat=cs.CL` 和 list 页面路径（`fetch_papers.py`）
- 更新页面标题、README（`main.py`、`README.md`、workflow 名称）

**更换/增加标签**：
- 修改 LLM prompt 中的标签定义（`translate.py`）
- 同步更新统计和展示逻辑（`main.py`、`generate_html.py`）

若需完全通用化，可将 `cs.CL` 等参数抽成环境变量或配置文件，无需改动代码即可切换类别。

import os
import json
import time
from openai import OpenAI

BATCH_SIZE = 5


def get_client():
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("环境变量 DASHSCOPE_API_KEY 未设置")
    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


def translate_papers(papers, model="qwen-flash"):
    client = get_client()
    to_translate = [(i, p) for i, p in enumerate(papers) if not p.get("title_translated")]

    if not to_translate:
        print("没有需要翻译的论文")
        return papers

    print(f"需要翻译 {len(to_translate)} 篇论文 (每批 {BATCH_SIZE} 篇)...")
    batches = [to_translate[i:i + BATCH_SIZE] for i in range(0, len(to_translate), BATCH_SIZE)]

    for batch_idx, batch in enumerate(batches):
        tasks = [{"index": i, "arxiv_id": p["arxiv_id"], "title": p["title"], "summary": p["summary"]}
                 for i, p in batch]

        prompt_parts = []
        for t in tasks:
            prompt_parts.append(f'[{t["index"]}] arxiv_id: {t["arxiv_id"]}')
            prompt_parts.append(f'title: {t["title"]}')
            prompt_parts.append(f'abstract: {t["summary"]}')
            prompt_parts.append("---")

        prompt = f"""你是一个学术翻译专家。请将以下 {len(tasks)} 篇英文论文的标题和摘要翻译成中文，保持学术严谨性。

返回格式为 JSON 数组，每个元素包含 "index", "title", "summary" 三个字段，其中 index 对应输入编号。

输入：
{chr(10).join(prompt_parts)}

请只返回 JSON 数组。"""

        for attempt in range(3):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.05,
                    response_format={"type": "json_object"},
                )
                content = resp.choices[0].message.content.strip()

                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
                    if content.endswith("```"):
                        content = content[:-3]

                result = json.loads(content)
                results_list = result if isinstance(result, list) else result.get("results", [])

                for item in results_list:
                    idx = item.get("index")
                    if idx is None:
                        continue
                    papers[idx]["title_translated"] = item.get("title", "")
                    papers[idx]["summary_translated"] = item.get("summary", "")

                translated = len(results_list)
                print(f"  批次 {batch_idx+1}/{len(batches)}: 翻译 {translated} 篇 ✓")
                break
            except Exception as e:
                print(f"  批次 {batch_idx+1} 失败 (尝试 {attempt+1}/3): {e}")
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
        else:
            print(f"  批次 {batch_idx+1} 翻译失败，跳过")

    return papers

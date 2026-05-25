import re

TAG_RULES = {
    "agent-benchmark": [
        r"agent\s*bench",
        r"agentbench",
        r"agent.*(?:evaluat|benchmark|assessment)",
        r"benchmark.*agent",
    ],
    "agent-memory": [
        r"agent.*(?:memory|memorization|memor)",
        r"(?:memory|memor).*(?:agent|rag)",
        r"memory.augmented.*agent",
        r"memory.*agent",
    ],
    "agentic-rl": [
        r"agentic.*(?:reinforcement\s*learning|rl)",
        r"(?:reinforcement\s*learning|rl).*agent",
        r"agent.*(?:reinforcement\s*learning|rl)",
    ],
}


def tag_papers(papers):
    for paper in papers:
        text = f"{paper['title']} {paper['summary']}".lower()
        tags = []
        for tag, patterns in TAG_RULES.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    tags.append(tag)
                    break
        paper["tags"] = tags
    return papers

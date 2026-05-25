import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

LIST_URL = "https://arxiv.org/list/cs.CL/recent"
API_URL = "https://export.arxiv.org/api/query"
HEADERS = {"User-Agent": "Mozilla/5.0"}

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _request(url, **kwargs):
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", 30)
    env_backup = {}
    for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        env_backup[k] = os.environ.pop(k, None)
    try:
        return requests.get(url, **kwargs)
    finally:
        for k, v in env_backup.items():
            if v is not None:
                os.environ[k] = v


def extract_papers(html):
    soup = BeautifulSoup(html, "html.parser")
    dl = soup.find("dl", id="articles")
    if not dl:
        return None, [], 0, 0

    first_h3 = dl.find("h3")
    if not first_h3:
        return None, [], 0, 0

    h3_text = first_h3.get_text(strip=True)
    m_date = re.match(r"([A-Za-z]+,\s+\d+\s+[A-Za-z]+\s+\d{4})", h3_text)
    if not m_date:
        return None, [], 0, 0
    date_str = m_date.group(1)

    m_total = re.search(r"(?:of|of first)\s+(\d+)\s+entries", h3_text)
    total = int(m_total.group(1)) if m_total else 0

    m_shown = re.search(r"showing(?:\s+first)?\s+(\d+)", h3_text)
    shown = int(m_shown.group(1)) if m_shown else 0

    dts, dds = [], []
    curr = first_h3.find_next_sibling()
    while curr and curr.name != "h3":
        if curr.name == "dt":
            dts.append(curr)
        elif curr.name == "dd":
            dds.append(curr)
        curr = curr.find_next_sibling()

    papers = []
    for i, dt in enumerate(dts):
        id_link = dt.find("a", id=True)
        if not id_link:
            continue
        p = {"arxiv_id": id_link["id"], "summary": "", "published": "", "published_date": ""}

        if i < len(dds):
            dd = dds[i]
            title_div = dd.find("div", class_="list-title")
            p["title"] = re.sub(r"^Title:\s*", "", title_div.get_text(" ", strip=True)) if title_div else ""

            authors_div = dd.find("div", class_="list-authors")
            p["authors"] = [a.get_text(strip=True) for a in authors_div.find_all("a")] if authors_div else []

            subjects_div = dd.find("div", class_="list-subjects")
            if subjects_div:
                text = re.sub(r"^Subjects:\s*", "", subjects_div.get_text(" ", strip=True))
                p["categories"] = [s.strip() for s in text.split(";")]
                p["primary_category"] = p["categories"][0] if p["categories"] else ""
            else:
                p["categories"] = []
                p["primary_category"] = ""

            comments_div = dd.find("div", class_="list-comments")
            p["comment"] = re.sub(r"^Comments:\s*", "", comments_div.get_text(" ", strip=True)) if comments_div else ""

        p.setdefault("title", "")
        p.setdefault("authors", [])
        p.setdefault("categories", [])
        p.setdefault("primary_category", "")
        p.setdefault("comment", "")
        papers.append(p)

    return date_str, papers, shown, total


def fetch_abstracts(arxiv_ids):
    if not arxiv_ids:
        return {}
    result = {}
    for i in range(0, len(arxiv_ids), 50):
        batch = arxiv_ids[i:i + 50]
        url = f"{API_URL}?id_list={','.join(batch)}&max_results={len(batch)}"

        for retry in range(4):
            try:
                resp = _request(url)
                if resp.status_code == 429:
                    if retry < 3:
                        print(f"  API 限流，等待 60s 后重试 ({retry+1}/3)...")
                        time.sleep(60)
                        continue
                    print("  重试耗尽，跳过该批次摘要获取")
                    break
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
                for entry in root.findall("atom:entry", NS):
                    eid = entry.find("atom:id", NS).text.strip().split("/")[-1].split("v")[0]
                    summary = entry.find("atom:summary", NS).text.strip().replace("\n", " ")
                    published = entry.find("atom:published", NS).text.strip()
                    result[eid] = {"summary": summary, "published": published, "published_date": published[:10]}
                break
            except Exception as e:
                print(f"  API 请求失败: {e}")
                if retry < 3:
                    time.sleep(60)
                else:
                    print("  重试耗尽，跳过该批次")

        time.sleep(2)
    return result


def fetch_today_papers():
    resp = _request(f"{LIST_URL}?show=250")
    resp.raise_for_status()
    date_str, papers, shown, total = extract_papers(resp.text)
    if not papers:
        return None, []

    # Pagination: if shown < total, fetch remaining pages
    while shown < total:
        remaining = total - shown
        next_url = f"{LIST_URL}?skip={shown}&show={remaining + 50}"
        try:
            resp = _request(next_url)
            resp.raise_for_status()
            _, extra, _, _ = extract_papers(resp.text)
        except Exception:
            break

        if not extra:
            break

        n_take = min(len(extra), remaining)
        papers.extend(extra[:n_take])
        shown += n_take

        need = total - shown
        if need <= 0:
            break

    time.sleep(2)
    ids = [p["arxiv_id"] for p in papers]
    abstracts = fetch_abstracts(ids)

    for p in papers:
        if p["arxiv_id"] in abstracts:
            p.update(abstracts[p["arxiv_id"]])

    return date_str, papers


def _extract_from_h3(h3_tag):
    dts, dds = [], []
    curr = h3_tag.find_next_sibling()
    while curr and curr.name != "h3":
        if curr.name == "dt":
            dts.append(curr)
        elif curr.name == "dd":
            dds.append(curr)
        curr = curr.find_next_sibling()

    papers = []
    for i, dt in enumerate(dts):
        id_link = dt.find("a", id=True)
        if not id_link:
            continue
        p = {"arxiv_id": id_link["id"], "summary": "", "published": "", "published_date": ""}
        if i < len(dds):
            dd = dds[i]
            title_div = dd.find("div", class_="list-title")
            p["title"] = re.sub(r"^Title:\s*", "", title_div.get_text(" ", strip=True)) if title_div else ""
            authors_div = dd.find("div", class_="list-authors")
            p["authors"] = [a.get_text(strip=True) for a in authors_div.find_all("a")] if authors_div else []
            subjects_div = dd.find("div", class_="list-subjects")
            if subjects_div:
                text = re.sub(r"^Subjects:\s*", "", subjects_div.get_text(" ", strip=True))
                p["categories"] = [s.strip() for s in text.split(";")]
                p["primary_category"] = p["categories"][0] if p["categories"] else ""
            else:
                p["categories"] = []
                p["primary_category"] = ""
            comments_div = dd.find("div", class_="list-comments")
            p["comment"] = re.sub(r"^Comments:\s*", "", comments_div.get_text(" ", strip=True)) if comments_div else ""
        p.setdefault("title", "")
        p.setdefault("authors", [])
        p.setdefault("categories", [])
        p.setdefault("primary_category", "")
        p.setdefault("comment", "")
        papers.append(p)
    return papers


def fetch_papers_by_date(target_date):
    from datetime import datetime
    target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    expected_label = target_dt.strftime("%a, %d %b %Y")

    skip = 0
    while True:
        resp = _request(f"{LIST_URL}?skip={skip}&show=250")
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        dl = soup.find("dl", id="articles")
        if not dl:
            break

        h3 = dl.find("h3")
        if not h3:
            break

        h3_text = h3.get_text(strip=True)
        m_date = re.match(r"([A-Za-z]+,\s+\d+\s+[A-Za-z]+\s+\d{4})", h3_text)
        if not m_date:
            break

        page_date_label = m_date.group(1)
        if page_date_label == expected_label:
            papers = _extract_from_h3(h3)
            ids = [p["arxiv_id"] for p in papers]
            abstracts = fetch_abstracts(ids)
            for p in papers:
                if p["arxiv_id"] in abstracts:
                    p.update(abstracts[p["arxiv_id"]])
            return page_date_label, papers

        # Get total entries for this page to compute next skip
        m_total = re.search(r"(?:of|of first)\s+(\d+)\s+entries", h3_text)
        if not m_total:
            break
        total = int(m_total.group(1))
        skip += total

    return target_date, []

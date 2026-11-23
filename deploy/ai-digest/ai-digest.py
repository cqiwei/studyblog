#!/usr/bin/env python3
"""AI 前哨日报生成器。

每天凌晨（北京时间 01:00，由 ai-digest.timer 调度）：
  ① 拉取各信息源（RSS / HN / arXiv / GitHub）
  ② sqlite 去重（保留 90 天）
  ③ 按来源权重 + 新鲜度挑选 Top N
  ④ 调 LLM 总结成一篇中文日报（OpenAI 兼容接口：默认魔搭免费额度，
     没配 key 就发纯聚合版）
  ⑤ git 提交推送 → hugo 构建 → 翻 release 软链 → purge Cloudflare

配置从 /etc/ai-digest.conf 读（KEY=VALUE），也认环境变量。
--dry-run 只抓取和挑选，不写库、不发布。
"""

import email.utils
import hashlib
import html as html_mod
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------- 配置

CONF_FILE = "/etc/ai-digest.conf"
DRY_RUN = "--dry-run" in sys.argv
REPAIR = "--repair" in sys.argv

REPO_DIR = os.environ.get("DIGEST_REPO", "/opt/blogrepo")
SEEN_DB = os.environ.get("DIGEST_SEEN_DB", "/var/lib/ai-digest/seen.db")
RELEASE_ROOT = "/var/www/blog/releases"
CURRENT_LINK = "/var/www/blog/current"
# LLM：OpenAI 兼容接口即可。默认魔搭（每天免费额度），
# 也可以换 DeepSeek 官方（LLM_BASE_URL=https://api.deepseek.com/v1）
LLM_API_KEY = os.environ.get("LLM_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api-inference.modelscope.cn/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "ZhipuAI/GLM-5.2")
# 主模型额度用光（429）时按顺序换模型，别直接退化成没有点评的聚合版
LLM_FALLBACKS = os.environ.get(
    "LLM_FALLBACKS", "Qwen/Qwen3.5-122B-A10B,deepseek-ai/DeepSeek-V4.1-Flash-1017")
LLM_RETRY_SLEEP = int(os.environ.get("LLM_RETRY_SLEEP", "20"))
# 聚合版正文里的标记，--repair 靠它认出「这篇还没点评」
FALLBACK_MARK = "<!-- digest:fallback -->"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_ZONE_NAME = os.environ.get("CF_ZONE_NAME", "aiqivy.com")
RSSHUB_URLS = [u for u in os.environ.get("AI_RSSHUB_URLS", "").split(",") if u]

NOW = datetime.now(timezone.utc)
BEIJING = timezone(timedelta(hours=8))
TODAY = NOW.astimezone(BEIJING).strftime("%Y-%m-%d")
WINDOW_HOURS = 36  # 拉最近 36 小时，覆盖昨天一整天

UA = "Mozilla/5.0 (compatible; aiqivy-digest/1.0; +https://aiqivy.com)"

# (名字, URL, 权重)。机器之心官方 RSS 已下线（返回 HTML 落地页），
# 想要它就走 AI_RSSHUB_URLS=https://rsshub.app/jiqizhixin
FEEDS = [
    ("量子位", "https://www.qbitai.com/feed", 1.2),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/", 1.0),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", 1.0),
]

# 标题里带这些词的加分
HOT_WORDS = re.compile(
    r"AGI|GPT|OpenAI|Anthropic|Claude|Gemini|DeepSeek|Qwen|Llama|"
    r"Sora|Midjourney|Copilot|agent|Agent|智能体|大模型|多模态|"
    r"推理|芯片|算力|开源", re.I)

AI_REPO_WORDS = re.compile(
    r"\bai\b|llm|gpt|agent|rag|diffusion|transformer|mcp|claude|"
    r"openai|gemini|qwen|deepseek|stable-?diffusion|whisper|embedding", re.I)


def log(msg):
    print(f"[{NOW.astimezone(BEIJING).strftime('%H:%M:%S')}] {msg}", flush=True)


def load_conf():
    """把 /etc/ai-digest.conf 的 KEY=VALUE 读进环境（已存在的环境变量优先）。"""
    if not os.path.exists(CONF_FILE):
        return
    with open(CONF_FILE) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
    globals().update(
        LLM_API_KEY=os.environ.get("LLM_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", ""),
        LLM_BASE_URL=os.environ.get("LLM_BASE_URL", "https://api-inference.modelscope.cn/v1"),
        LLM_MODEL=os.environ.get("LLM_MODEL", "ZhipuAI/GLM-5.2"),
        LLM_FALLBACKS=os.environ.get(
            "LLM_FALLBACKS", "Qwen/Qwen3.5-122B-A10B,deepseek-ai/DeepSeek-V4.1-Flash-1017"),
        LLM_RETRY_SLEEP=int(os.environ.get("LLM_RETRY_SLEEP", "20")),
        GITHUB_TOKEN=os.environ.get("GITHUB_TOKEN", ""),
        CF_API_TOKEN=os.environ.get("CF_API_TOKEN", ""),
        RSSHUB_URLS=[u for u in os.environ.get("AI_RSSHUB_URLS", "").split(",") if u],
    )


def http_get(url, timeout=20, headers=None):
    hdrs = {"User-Agent": UA}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def clean_text(text, limit=280):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)          # 去 HTML 标签
    text = html_mod.unescape(text)                 # 去 HTML 实体
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


# ---------------------------------------------------------------- 解析 RSS / Atom

def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _child_text(node, name):
    for child in node:
        if _local(child.tag) == name and child.text:
            return child.text.strip()
    return ""


def _entry_link(node):
    for child in node:
        if _local(child.tag) != "link":
            continue
        rel = child.get("rel", "alternate")
        href = child.get("href") or (child.text or "").strip()
        if href and rel == "alternate":
            return href
        if href and rel != "self":
            return href
    return ""


def _entry_time(node):
    for name in ("pubDate", "published", "updated", "date"):
        raw = _child_text(node, name)
        if not raw:
            continue
        try:  # Atom 的 ISO 8601：2026-11-20T17:59:59Z
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
        try:  # RSS 的 RFC 822：Sat, 21 Nov 2026 09:00:00 +0000
            dt = email.utils.parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (TypeError, ValueError):
            continue
    return None


def parse_feed(data):
    """RSS2 / Atom / RDF 通吃，返回 [{title, url, published, summary}]。"""
    items = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return items
    for node in root.iter():
        if _local(node.tag) not in ("item", "entry"):
            continue
        title = clean_text(_child_text(node, "title"), 200)
        url = _entry_link(node)
        if not title or not url or url.startswith("#"):
            continue
        items.append({
            "title": title,
            "url": url,
            "published": _entry_time(node),
            "summary": clean_text(_child_text(node, "description")
                                  or _child_text(node, "summary")
                                  or _child_text(node, "content")),
        })
    return items


# ---------------------------------------------------------------- 抓取器

def fetch_feeds():
    items = []
    for name, url, weight in FEEDS + [(f"RSSHub:{u}", u, 1.0) for u in RSSHUB_URLS]:
        try:
            entries = parse_feed(http_get(url))
            fresh = 0
            for e in entries:
                e["source"], e["weight"] = name, weight
                if e["published"] and NOW - e["published"] <= timedelta(hours=WINDOW_HOURS):
                    fresh += 1
                    items.append(e)
            log(f"{name}: {len(entries)} 条，窗口内 {fresh} 条")
        except Exception as exc:  # 单个源失败不影响整体
            log(f"WARN {name}: {exc}")
    return items


def fetch_hackernews():
    """HN 用 Algolia API，比 RSS 干净，还能按热度过滤。"""
    items, seen_urls = [], set()
    for query, min_points in (("AI", 100), ("LLM", 80), ("OpenAI", 120)):
        q = urllib.parse.quote(query)
        url = ("https://hn.algolia.com/api/v1/search_by_date?tags=story"
               f"&query={q}&hitsPerPage=30&numericFilters=points%3E{min_points}")
        try:
            data = json.loads(http_get(url))
            for hit in data.get("hits", []):
                link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                if link in seen_urls:
                    continue
                seen_urls.add(link)
                ts = hit.get("created_at_i")
                items.append({
                    "source": "Hacker News", "weight": 1.0,
                    "title": clean_text(hit.get("title"), 200),
                    "url": link,
                    "published": datetime.fromtimestamp(ts, timezone.utc) if ts else None,
                    "summary": f"{hit.get('points', 0)} 分 / {hit.get('num_comments', 0)} 评",
                })
        except Exception as exc:
            log(f"WARN HN({query}): {exc}")
    log(f"Hacker News: {len(items)} 条")
    return items


def fetch_arxiv():
    """arXiv 周末不发论文，窗口放宽到 96h，靠打分挑新鲜的。"""
    cats = "+OR+".join(f"cat:{c}" for c in ("cs.AI", "cs.CL", "cs.LG"))
    url = ("http://export.arxiv.org/api/query?search_query=" + cats
           + "&start=0&max_results=40&sortBy=submittedDate&sortOrder=descending")
    try:
        entries = parse_feed(http_get(url))
        for e in entries:
            e["source"], e["weight"], e["no_window"] = "arXiv", 0.6, True
        fresh = [e for e in entries
                 if e["published"] and NOW - e["published"] <= timedelta(hours=96)]
        log(f"arXiv: {len(entries)} 条，96h 内 {len(fresh)} 条")
        return fresh
    except Exception as exc:
        log(f"WARN arXiv: {exc}")
        return []


def fetch_github():
    day_ago = (NOW - timedelta(days=1)).strftime("%Y-%m-%d")
    q = urllib.parse.quote(f"created:>{day_ago} stars:>30")
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=30"
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    items = []
    try:
        data = json.loads(http_get(url, headers=headers))
        for repo in data.get("items", []):
            text = f"{repo.get('name')} {repo.get('description') or ''}"
            if not AI_REPO_WORDS.search(text):
                continue
            desc = clean_text(repo.get("description"), 200)
            items.append({
                "source": "GitHub", "weight": 1.0,
                "title": f"{repo.get('full_name')} ★{repo.get('stargazers_count')}",
                "url": repo.get("html_url"),
                "published": None,
                "summary": desc or "（暂无描述）",
            })
        log(f"GitHub: {len(items)} 条 AI 相关")
    except Exception as exc:
        log(f"WARN GitHub: {exc}")
    return items


# ---------------------------------------------------------------- 去重 / 挑选

def seen_connect():
    os.makedirs(os.path.dirname(SEEN_DB), exist_ok=True)
    conn = sqlite3.connect(SEEN_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS seen (url_hash TEXT PRIMARY KEY, first_seen TEXT)")
    conn.execute("DELETE FROM seen WHERE first_seen < ?",
                 ((NOW - timedelta(days=90)).strftime("%Y-%m-%d"),))
    return conn


def url_hash(url):
    return hashlib.sha1(url.encode()).hexdigest()


def dedup(items, conn):
    kept = []
    for item in items:
        h = url_hash(item["url"])
        if conn.execute("SELECT 1 FROM seen WHERE url_hash=?", (h,)).fetchone():
            continue
        item["hash"] = h
        kept.append(item)
    return kept


def score(item):
    s = item.get("weight", 1.0)
    if item.get("published"):
        hours = (NOW - item["published"]).total_seconds() / 3600
        s += max(0.0, 1.5 - hours / 24)  # 越新鲜分越高
    if HOT_WORDS.search(item["title"]):
        s += 0.3
    return s


def pick(items, limit=22):
    items.sort(key=score, reverse=True)
    caps = {"arXiv": 4, "GitHub": 4, "Hacker News": 5}
    # 给论文留位子（否则打分排不进前 22）
    reserve = min(4, sum(1 for i in items if i["source"] == "arXiv"))
    picked, counts, non_arxiv = [], {}, 0
    for item in items:
        if len(picked) >= limit:
            break
        src = item["source"]
        if counts.get(src, 0) >= caps.get(src, 99):
            continue
        if src != "arXiv" and non_arxiv >= limit - reserve:
            continue
        counts[src] = counts.get(src, 0) + 1
        if src != "arXiv":
            non_arxiv += 1
        picked.append(item)
    # 板块保底：论文 / 开源 / HN 至少 N 条（有货的话），不让日报出现空板块
    mins = {"arXiv": 4, "GitHub": 3, "Hacker News": 2}
    for src, minimum in mins.items():
        have = sum(1 for i in picked if i["source"] == src)
        target = min(minimum, sum(1 for i in items if i["source"] == src))
        for item in items:
            if have >= target:
                break
            if item["source"] == src and item not in picked:
                picked.append(item)
                counts[src] = counts.get(src, 0) + 1
                have += 1
    # 中文来源保底
    cn_sources = {"量子位", "机器之心"}
    cn_target = min(3, sum(1 for i in items if i["source"] in cn_sources))
    cn = sum(1 for i in picked if i["source"] in cn_sources)
    if cn < cn_target:
        for item in items:
            if item in picked:
                continue
            if item["source"] in cn_sources:
                picked.append(item)
                cn += 1
                if cn >= cn_target:
                    break
    return picked


def mark_seen(conn, items):
    day = NOW.strftime("%Y-%m-%d")
    conn.executemany(
        "INSERT OR IGNORE INTO seen (url_hash, first_seen) VALUES (?, ?)",
        [(i["hash"], day) for i in items])
    conn.commit()


# ---------------------------------------------------------------- LLM 总结

def build_material(items):
    lines = []
    for i, item in enumerate(items, 1):
        when = ""
        if item.get("published"):
            when = item["published"].astimezone(BEIJING).strftime("%m-%d %H:%M")
        lines.append(f"{i}. [{item['source']}] {item['title']}（{when}）\n"
                     f"   摘要：{item['summary']}\n"
                     f"   链接：{item['url']}")
    return "\n".join(lines)


def deepseek_summarize(items):
    material = build_material(items)
    return run_llm(material, system_prompt=DAILY_SYSTEM, user_prompt=DAILY_USER)


DAILY_SYSTEM = (
    "你是一位中文科技编辑，负责给「AI 前哨日报」写内容。"
    "只根据提供的材料写作，不编造任何事实；"
    "输出纯 markdown 正文（不要 front matter、不要开场白）；"
    "每条信息保留原文链接。")

DAILY_USER = (
    "下面是过去 36 小时收集到的 AI 信息。请写成一篇日报，结构：\n"
    "## 今日看点\n3-5 条一句话要点（挑最有价值的）\n"
    "## 媒体动态\n（量子位/TechCrunch/The Verge/HN）\n"
    "## 论文速览\n（arXiv，每条一两句人话概括）\n"
    "## 开源热门\n（GitHub 项目）\n\n"
    "格式：**标题** — 一两句中文摘要。([来源](链接))\n"
    "没有内容的板块直接省略。材料：\n\n")


def llm_models():
    """主模型 + 兜底模型，去重保序。"""
    out = []
    for name in [LLM_MODEL] + LLM_FALLBACKS.split(","):
        name = name.strip()
        if name and name not in out:
            out.append(name)
    return out


def _chat(model, messages, max_tokens, timeout=300):
    payload = {
        "model": model,
        "temperature": 0.5,
        # 推理型模型会把思维链算进 max_tokens，给足余量防止正文被截断
        "max_tokens": max_tokens,
        "messages": messages,
    }
    req = urllib.request.Request(
        LLM_BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {LLM_API_KEY}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    choice = data["choices"][0]
    content = (choice["message"].get("content") or "").strip()
    finish = choice.get("finish_reason", "")
    if len(content) < 200:  # 推理 token 吃光预算时正文会只剩个 "##"
        raise ValueError(
            f"正文过短（finish={finish}, content_len={len(content)}），疑似被截断")
    return content


def run_llm(material, system_prompt, user_prompt, max_tokens=12000):
    """按模型链依次尝试：429/5xx 先退避重试一次，再换下一个模型。

    返回 (正文, 实际使用的模型名)。全部失败抛 RuntimeError。
    """
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt + material}]
    errors = []
    for model in llm_models():
        for attempt in (1, 2):
            try:
                content = _chat(model, messages, max_tokens)
                log(f"  [{model}] 第 {attempt} 次尝试成功，正文 {len(content)} 字")
                return content, model
            except urllib.error.HTTPError as exc:
                try:
                    detail = exc.read().decode("utf-8", "replace")[:120]
                except Exception:
                    detail = ""
                errors.append(f"{model} HTTP {exc.code} {detail}")
                log(f"  [{model}] 第 {attempt} 次失败：HTTP {exc.code} {detail}")
                if exc.code in (429, 500, 502, 503, 504) and attempt == 1:
                    time.sleep(LLM_RETRY_SLEEP)
                    continue
                break
            except (ValueError, urllib.error.URLError, TimeoutError, OSError) as exc:
                errors.append(f"{model} {type(exc).__name__}: {exc}")
                log(f"  [{model}] 第 {attempt} 次失败：{exc}")
                break
    raise RuntimeError("所有模型都失败：" + " ｜ ".join(errors))


def aggregate_fallback(items):
    """没配 LLM key 或总结失败时的纯聚合版（带标记，后面会自动补写点评）。"""
    by_src = {}
    for item in items:
        by_src.setdefault(item["source"], []).append(item)
    parts = [FALLBACK_MARK,
             "> **本期 AI 点评没生成**（总结接口额度耗尽或临时故障），"
             "下面是原始清单；系统会在几小时内自动重试，成功后替换成本文。\n"]
    for src, group in by_src.items():
        parts.append(f"\n## {src}\n")
        for item in group:
            parts.append(f"- **{item['title']}**（{item['summary']}）"
                         f"([原文]({item['url']}))")
    return "\n".join(parts)


# ---------------------------------------------------------------- 发布

def git(*args, cwd=REPO_DIR):
    return subprocess.run(["git", *args], cwd=cwd,
                          capture_output=True, text=True, check=True)


def publish(body, items, force=False):
    filename = f"ai-daily-{TODAY}.md"
    rel = f"content/ai/{filename}"
    path = os.path.join(REPO_DIR, rel)
    if os.path.exists(path) and not force:
        log(f"{rel} 已存在，跳过发布（避免覆盖）")
        return

    n_media = sum(1 for i in items if i["source"] not in ("arXiv", "GitHub"))
    n_paper = sum(1 for i in items if i["source"] == "arXiv")
    n_repo = sum(1 for i in items if i["source"] == "GitHub")
    desc = f"今日 {len(items)} 条：媒体 {n_media} · 论文 {n_paper} · 开源 {n_repo}"

    fm = (f'---\ntitle: "AI 前哨日报 · {TODAY}"\n'
          f'date: {TODAY}T01:05:00+08:00\n'
          f'draft: false\n'
          f'tags: ["AI", "日报"]\n'
          f'description: "{desc}"\n---\n\n')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(fm + body + "\n")
    log(f"文章已写入 {rel}")

    git("add", rel)
    msg = f"AI 前哨日报 {TODAY}（补 AI 点评）" if force else f"AI 前哨日报 {TODAY}（{len(items)} 条）"
    git("-c", "user.name=ai-digest", "-c", "user.email=digest@aiqivy.com",
        "commit", "-m", msg)
    git("pull", "--rebase", "origin", "main")
    git("push", "origin", "main")
    log("git push 完成")

    build_dir = f"/tmp/blog-build-{int(time.time())}"
    release_dir = os.path.join(RELEASE_ROOT, NOW.astimezone(BEIJING).strftime("%Y%m%d-%H%M%S"))
    subprocess.run(["/usr/local/bin/hugo", "--quiet", "--destination", build_dir],
                   cwd=REPO_DIR, check=True, capture_output=True)
    subprocess.run(["mkdir", "-p", release_dir], check=True)
    subprocess.run(["rsync", "-a", "--delete", build_dir + "/", release_dir + "/"], check=True)
    subprocess.run(["ln", "-sfn", release_dir, CURRENT_LINK], check=True)
    log(f"release {release_dir} 上线")
    purge_cache()


def purge_cache():
    if not CF_API_TOKEN:
        log("WARN 未配置 CF_API_TOKEN，跳过缓存清理（文章最长 1h 后可见）")
        return
    try:
        req = urllib.request.Request(
            f"https://api.cloudflare.com/client/v4/zones?name={CF_ZONE_NAME}",
            headers={"Authorization": f"Bearer {CF_API_TOKEN}"})
        zone_id = json.loads(urllib.request.urlopen(req, timeout=20).read())["result"][0]["id"]
        req = urllib.request.Request(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache",
            data=json.dumps({"purge_everything": True}).encode(),
            headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                     "Content-Type": "application/json"},
            method="POST")
        json.loads(urllib.request.urlopen(req, timeout=30).read())
        log("Cloudflare 缓存已清理")
    except Exception as exc:
        log(f"WARN purge 失败（不影响发布）: {exc}")


# ---------------------------------------------------------------- 主流程

def main():
    load_conf()
    if DRY_RUN:
        log("== dry-run：只抓取和挑选，不写库不发布 ==")

    rel = f"content/ai/ai-daily-{TODAY}.md"
    path = os.path.join(REPO_DIR, rel)
    if REPAIR:
        if not os.path.exists(path):
            log("今天还没有日报，跳过补写")
            return
        with open(path, encoding="utf-8") as fh:
            existing = fh.read()
        if FALLBACK_MARK not in existing and "纯聚合版" not in existing:
            log("今天的日报已经有 AI 点评，跳过补写")
            return
        log("== repair：检测到聚合版日报，尝试补写 AI 点评 ==")

    items = (fetch_feeds() + fetch_hackernews() + fetch_arxiv() + fetch_github())
    log(f"共抓到 {len(items)} 条（窗口 {WINDOW_HOURS}h）")
    if not items:
        log("没有抓到任何内容，退出")
        return

    conn = seen_connect()
    try:
        # 全局再按窗口过滤一次（arXiv 周末不发论文，单独放宽，见 no_window）
        in_window = [i for i in items
                     if i.get("no_window")
                     or not i.get("published")
                     or NOW - i["published"] <= timedelta(hours=WINDOW_HOURS)]
        if REPAIR:
            fresh = in_window  # 补写时不能用 seen.db 去重，否则全被过滤掉
            log(f"补写模式：窗口内 {len(fresh)} 条全部参与挑选")
        else:
            fresh = dedup(in_window, conn)
            log(f"窗口内 {len(in_window)} 条，去重后剩 {len(fresh)} 条")
        if not fresh:
            log("全部都已见过，今天不生成日报")
            return
        picked = pick(fresh)
        by_src = {}
        for item in picked:
            by_src[item["source"]] = by_src.get(item["source"], 0) + 1
        log(f"挑选出 {len(picked)} 条：" + ", ".join(f"{s}×{n}" for s, n in by_src.items()))
        for i in picked[:5]:
            log(f"  top: [{i['source']}] {i['title'][:60]}")

        if DRY_RUN:
            print(build_material(picked))
            return

        body = None
        if LLM_API_KEY:
            try:
                body, used = deepseek_summarize(picked)
                log(f"LLM 总结完成（{used} @ {LLM_BASE_URL}）")
            except Exception as exc:
                log(f"WARN LLM 失败: {exc}")
        else:
            log("WARN 未配置 LLM_API_KEY")

        if body is None:
            if REPAIR:
                log("补写失败，保留聚合版，等下一次重试")
                return
            body = aggregate_fallback(picked)

        if not REPAIR:
            mark_seen(conn, picked)
        publish(body, picked, force=REPAIR)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

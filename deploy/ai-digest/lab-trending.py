#!/usr/bin/env python3
"""灵光一现：GitHub Trending 每日趋势 + 用途点评。

每天抓 github.com/trending（daily）前 N 个仓库，拉各自的 README，
交给 LLM 写「是什么 / 能拿来干嘛 / 适合谁」的点评，
发布到 content/lab/git-trending-YYYY-MM-DD.md。

配置复用 /etc/ai-digest.conf（LLM_API_KEY / LLM_BASE_URL / LLM_MODEL /
CF_API_TOKEN），与 ai-digest.py 同一套凭据，纯标准库。
"""

import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------- 配置

CONF_FILE = "/etc/ai-digest.conf"
DRY_RUN = "--dry-run" in sys.argv
REPAIR = "--repair" in sys.argv
TOP_N = int(os.environ.get("TRENDING_TOP_N", "10"))

REPO_DIR = os.environ.get("DIGEST_REPO", "/opt/blogrepo")
RELEASE_ROOT = "/var/www/blog/releases"
CURRENT_LINK = "/var/www/blog/current"

LLM_API_KEY = os.environ.get("LLM_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api-inference.modelscope.cn/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "ZhipuAI/GLM-5.2")
# 主模型额度用光（429）时按顺序换模型，别直接退化成没有点评的列表版
LLM_FALLBACKS = os.environ.get(
    "LLM_FALLBACKS", "Qwen/Qwen3.5-122B-A10B,deepseek-ai/DeepSeek-V4.1-Flash-1017")
LLM_RETRY_SLEEP = int(os.environ.get("LLM_RETRY_SLEEP", "20"))
FALLBACK_MARK = "<!-- trending:fallback -->"
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_ZONE_NAME = os.environ.get("CF_ZONE_NAME", "aiqivy.com")

NOW = datetime.now(timezone.utc)
BEIJING = timezone(timedelta(hours=8))
TODAY = NOW.astimezone(BEIJING).strftime("%Y-%m-%d")

# github.com/trending 会给 curl 一类 UA 返回简化页，必须装成浏览器
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
README_NAMES = ["README.md", "README.zh-CN.md", "README_zh.md",
                "README.zh.md", "README.rst", "README"]
README_MAX = 4000


def log(msg):
    print(f"[{NOW.astimezone(BEIJING).strftime('%H:%M:%S')}] {msg}", flush=True)


def load_conf():
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
        CF_API_TOKEN=os.environ.get("CF_API_TOKEN", ""),
        CF_ZONE_NAME=os.environ.get("CF_ZONE_NAME", "aiqivy.com"),
    )


def http_get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ---------------------------------------------------------------- 抓取

def clean_text(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"\s+", " ", s).strip()


def fetch_trending():
    """抓 github.com/trending?since=daily，返回前 TOP_N 个仓库。"""
    page = http_get("https://github.com/trending?since=daily", timeout=30).decode("utf-8", "ignore")
    repos = []
    for chunk in page.split("<article")[1:]:
        m = re.search(
            r'<h2[^>]*>.*?<a[^>]+href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', chunk, re.S)
        if not m:
            continue
        path = m.group(1)
        desc_m = re.search(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', chunk, re.S)
        lang_m = re.search(r'itemprop="programmingLanguage">([^<]+)<', chunk)
        today_m = re.search(r'([\d,]+)\s*stars?\s*today', chunk)
        total_m = re.search(r'/stargazers[^"]*"[^>]*>(?:\s|<[^>]*>)*([\d,]+)', chunk)
        repos.append({
            "path": path,
            "url": f"https://github.com/{path}",
            "desc": clean_text(desc_m.group(1)) if desc_m else "",
            "lang": lang_m.group(1).strip() if lang_m else "",
            "total": total_m.group(1) if total_m else "?",
            "today": today_m.group(1) if today_m else "?",
        })
        if len(repos) >= TOP_N:
            break
    return repos


def fetch_readme(path):
    for name in README_NAMES:
        try:
            raw = http_get(
                f"https://raw.githubusercontent.com/{path}/HEAD/{name}",
                timeout=15).decode("utf-8", "ignore")
        except Exception:
            continue
        if not raw.strip():
            continue
        raw = re.sub(r"```.*?```", "", raw, flags=re.S)  # 代码块费 token 没必要给
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\n{2,}", "\n", raw).strip()
        return raw[:README_MAX]
    return ""


# ---------------------------------------------------------------- LLM

def build_material(repos):
    lines = []
    for rank, r in enumerate(repos, 1):
        lines.append(
            f"{rank}. {r['path']}（{r['lang'] or '语言未知'} · 总星 {r['total']} · 今日 +{r['today']}）\n"
            f"   简介：{r['desc'] or '（无）'}\n"
            f"   链接：{r['url']}\n"
            f"   README 摘录：{r['readme'][:1200] or '（未取到）'}")
    return "\n".join(lines)


def llm_models():
    out = []
    for name in [LLM_MODEL] + LLM_FALLBACKS.split(","):
        name = name.strip()
        if name and name not in out:
            out.append(name)
    return out


SYSTEM_PROMPT = (
    "你是博客「灵光一现」栏目的编辑，负责写 GitHub Trending 每日点评。"
    "只根据提供的材料写作，不编造功能、数字或没有依据的评价；"
    "点评要具体、有用，说清楚它是什么、能拿来干什么、适合谁。")

USER_PROMPT = (
    "下面是今天 GitHub Trending（日榜）排名靠前的仓库材料，"
    "含排名、简介、语言、总星数、今日新增星数和 README 摘录。"
    "请写一篇点评文章：\n"
    "1. 开头一段 2-3 句的今日趋势观察（归纳共同主题，不用逐个点名）。\n"
    "2. 按排名顺序逐个仓库，每节格式严格如下：\n"
    "### {排名}. [{owner}/{repo}](仓库链接)\n"
    "`{语言} · 总星 {总星数} · 今日 +{今日新增}`\n"
    "然后写 2-4 句用途点评：是什么、能拿来干什么、适合谁用；"
    "README 里有明确依据时才提成熟度/注意事项。\n"
    "3. 不要写结尾总结段，不要编造。材料：\n\n")


def _chat(model, messages, max_tokens=12000, timeout=300):
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


def subprocess_run_llm(material):
    """按模型链依次尝试，返回 (正文, 实际使用的模型名)。"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT + material}]
    errors = []
    for model in llm_models():
        for attempt in (1, 2):
            try:
                content = _chat(model, messages)
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


def aggregate_fallback(repos):
    """没配 LLM key 或点评失败时的纯列表版（带标记，后面会自动补写点评）。"""
    parts = [FALLBACK_MARK,
             "> **本期的用途点评没生成**（总结接口额度耗尽或临时故障），"
             "下面是趋势数据；系统会在几小时内自动重试，成功后替换成本文。\n"]
    for rank, r in enumerate(repos, 1):
        parts.append(
            f"### {rank}. [{r['path']}]({r['url']})\n"
            f"`{r['lang'] or '—'} · 总星 {r['total']} · 今日 +{r['today']}`\n\n"
            f"{r['desc'] or '（无简介）'}\n")
    return "\n".join(parts)


# ---------------------------------------------------------------- 发布

def git(*args):
    return subprocess.run(["git", *args], cwd=REPO_DIR,
                          capture_output=True, text=True, check=True)


def publish(body, repos, force=False):
    filename = f"git-trending-{TODAY}.md"
    rel = f"content/lab/{filename}"
    path = os.path.join(REPO_DIR, rel)
    if os.path.exists(path) and not force:
        log(f"{rel} 已存在，跳过发布（避免覆盖）")
        return

    when = NOW.astimezone(BEIJING).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    fm = (f'---\ntitle: "GitHub Trending 每日趋势 · {TODAY}"\n'
          f'date: {when}\n'
          f'draft: false\n'
          f'tags: ["GitHub", "开源", "趋势"]\n'
          f'description: "今日 GitHub 趋势 Top {len(repos)} 仓库与用途点评"\n---\n\n')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(fm + body + "\n")
    log(f"文章已写入 {rel}")

    git("add", rel)
    msg = (f"灵光一现：GitHub Trending 每日点评 {TODAY}（补点评）" if force
           else f"灵光一现：GitHub Trending 每日点评 {TODAY}")
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
        log("== dry-run：只抓取和取 README，不调用 LLM 不发布 ==")

    rel = f"content/lab/git-trending-{TODAY}.md"
    path = os.path.join(REPO_DIR, rel)
    if REPAIR:
        if not os.path.exists(path):
            log("今天还没有趋势点评，跳过补写")
            return 0
        with open(path, encoding="utf-8") as fh:
            existing = fh.read()
        if FALLBACK_MARK not in existing and "纯聚合版" not in existing:
            log("今天的趋势点评已生成，跳过补写")
            return 0
        log("== repair：检测到纯列表版，尝试补写点评 ==")

    repos = fetch_trending()
    log(f"GitHub Trending 抓到 {len(repos)} 个仓库")
    if not repos:
        log("ERROR 一个仓库都没解析到，可能是 GitHub 页面结构变了，需要检查正则")
        return 1
    for r in repos[:3]:
        log(f"  top: {r['path']}（{r['lang']} · +{r['today']} today）")

    log("拉取 README ...")
    for r in repos:
        r["readme"] = fetch_readme(r["path"])
    got = sum(1 for r in repos if r["readme"])
    log(f"README 取到 {got}/{len(repos)}")

    if DRY_RUN:
        print(build_material(repos)[:2000])
        return 0

    material = build_material(repos)
    body = None
    if LLM_API_KEY:
        try:
            body, used = subprocess_run_llm(material)
            log(f"LLM 点评完成（{used} @ {LLM_BASE_URL}）")
        except Exception as exc:
            log(f"WARN LLM 失败: {exc}")
    else:
        log("WARN 未配置 LLM_API_KEY")

    if body is None:
        if REPAIR:
            log("补写失败，保留列表版，等下一次重试")
            return 0
        body = aggregate_fallback(repos)

    publish(body, repos, force=REPAIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())

---
title: "GitHub Trending 每日趋势 · 2026-11-25"
date: 2026-11-25T01:36:24+08:00
draft: false
tags: ["GitHub", "开源", "趋势"]
description: "今日 GitHub 趋势 Top 10 仓库与用途点评"
---

今天的榜单几乎被 AI 代理技能包和框架占据——从安全研究、软件开发、图表绘制到跨平台信息检索，代理生态正在快速成型并渗透到各类具体工作流中。与此同时，让 AI 原生接入传统软件、从零训练小模型，以及经典的 Web 服务器和推理优化工具也持续受到关注。

### 1. [elementalsouls/Claude-BugHunter](https://github.com/elementalsouls/Claude-BugHunter)
`Python · 总星 21,059 · 今日 +1,833`
这是一个面向 Claude Code 的安全研究技能包，安装后让 Claude Code 具备类似资深 bug hunter 和红队操作员的能力。它打包了 84 个技能、15 个 slash 命令和 681 个公开报告模式，覆盖 24 个核心漏洞类别，还包含企业身份与基础设施攻击矩阵以及 Burp MCP 集成。适合安全研究员、bug bounty 猎人和红队操作员使用。README 明确提到该工具已在授权的红队和 bug hunting 任务以及公共训练平台（DVWA、OWASP Juice Shop、Hacker101 等）上经过实战测试。

### 2. [obra/superpowers](https://github.com/obra/superpowers)
`Shell · 总星 325,764 · 今日 +1,006`
这是一套面向编码代理的完整软件开发方法论，由可组合的技能和初始指令构成，确保代理按照结构化流程工作。它支持 Claude Code、Cursor、Codex、Gemini CLI、GitHub Copilot CLI 等十余种编码代理工具。适合想让 AI 编码代理更规范、更可靠地参与日常开发流程的工程师和团队使用。

### 3. [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
`Python · 总星 64,531 · 今日 +1,075`
这个项目的核心目标是让所有软件变成 Agent 原生——通过为各类软件生成 CLI 接口，让 AI 代理能够直接操作它们并产出真实成果物（如 CAD 构建、3D 场景、图表、字幕等）。它提供 CLI-Hub 供用户浏览、安装和管理社区构建的 CLI，也欢迎贡献者提交新的 CLI。适合想让 AI 代理自动操作各类桌面软件或在线服务的开发者和研究者。

### 4. [jingyaogong/minimind](https://github.com/jingyaogong/minimind)
`Python · 总星 70,054 · 今日 +727`
这是一个从零开始训练超小语言模型（约 64M 参数）的完整开源项目，主打极低成本和短时间上手。它覆盖了数据清洗、预训练、SFT、LoRA、RLHF（DPO/PPO/GRPO）、Tool Use、模型蒸馏等全链路代码，最小版本体积约为 GPT-3 的 1/2700。适合想从零理解大模型训练全流程的学习者和研究者，普通个人 GPU 即可跑通。

### 5. [cursor/plugins](https://github.com/cursor/plugins)
`TypeScript · 总星 19,103 · 今日 +359`
这是 Cursor 的插件规范和官方插件集合，每个插件是仓库根目录下的独立目录，带有自己的 manifest 文件。目前已包含教学、持续学习、团队工作流（CI、代码审查、发布）、深度安全审查（Thermos）等插件。适合 Cursor 用户，尤其是想扩展 Cursor 能力或建立团队标准化工作流的开发团队。

### 6. [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl)
`TypeScript · 总星 208,665 · 今日 +990`
这是一套为 AI 代理提供知识基础设施的工具，能搜索、抓取网页并访问 550+ 数据提供商，将网站转为干净的 markdown。它支持三种使用方式：本地单二进制运行（可作为 MCP 服务器接入代理）、托管云服务、以及完全自托管部署。适合需要为 AI 代理提供高质量网页数据抓取和搜索能力的开发者。

### 7. [nginx/nginx](https://github.com/nginx/nginx)
`C · 总星 33,166 · 今日 +158`
这是 NGINX 官方开源仓库，提供世界最流行的高性能 Web 服务器，同时可用作负载均衡器、反向代理、API 网关和内容缓存。采用简化的 BSD 类许可证，企业版由 F5 提供商业支持和培训。适合需要部署和管理 Web 服务、反向代理或 API 网关的运维和后端工程师。README 标注项目处于 Active 状态，已达到稳定可用并持续开发中。

### 8. [openvinotoolkit/openvino](https://github.com/openvinotoolkit/openvino)
`C++ · 总星 12,412 · 今日 +187`
这是 Intel 开源的深度学习推理优化和部署工具包，支持计算机视觉、语音识别、生成式 AI、NLP 等多种任务，覆盖大语言模型和小语言模型。它提供 PyPI、Conda、npm、Homebrew 等多渠道安装方式。适合需要在边缘设备或生产环境中优化 AI 模型推理性能并完成部署的工程师。

### 9. [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
`HTML · 总星 71,755 · 今日 +794`
这是一个面向 AI 编码代理的图表设计技能，支持 Claude Code、Codex、GitHub Copilot、Cursor 等多种工具。它能生成自包含的 HTML + SVG 图表文件，覆盖 52 种图表类型，可按品牌风格定制，不依赖 Mermaid。适合需要让 AI 代理直接产出高质量、可编辑图表的开发者和内容创作者。

### 10. [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
`Python · 总星 73,997 · 今日 +695`
这是一个 AI 代理驱动的搜索技能，能跨 Reddit、X、YouTube、HN、Polymarket 和网络研究任意主题，并按点赞、投票和真实资金信号排序，最终综合成有依据的摘要。它支持 Claude Code 以及 Codex、Cursor、Copilot、Gemini CLI 等 50+ 代理技能宿主，零配置即可使用部分数据源。适合需要快速了解某个话题近期热度走势和关键信息的研究者、产品经理和开发者。

---
title: "GitHub Trending 每日趋势 · 2026-11-28"
date: 2026-11-28T01:37:24+08:00
draft: false
tags: ["GitHub", "开源", "趋势"]
description: "今日 GitHub 趋势 Top 10 仓库与用途点评"
---

今天的 GitHub Trending 日榜上，"给 AI 编码代理装技能"是一条清晰的主线——从安全测试、图表生成到主题调研，各类可插拔的 Agent 技能包占据了大半席位。与此同时，让软件对 Agent 友好、从零训练小模型、推理优化等基础设施项目也持续受到关注，说明开发者既在打磨代理的能力边界，也在夯实底层支撑。

### 1. [elementalsouls/Claude-BugHunter](https://github.com/elementalsouls/Claude-BugHunter)
`Python · 总星 25,701 · 今日 +1,615`

一个面向 Claude Code 的技能包，装上之后让 Claude Code 像资深 bug 猎手或红队操作员一样工作。内置 85 个技能、16 个 slash 命令和 681 个已披露漏洞报告模式，覆盖 24 个核心漏洞类别，还包含企业身份与基础设施攻击矩阵及 Burp MCP 集成。适合安全研究员、bug bounty 猎人和红队操作员使用；README 明确提到已在授权的红队和 bug hunting 实战中测试过。

### 2. [obra/superpowers](https://github.com/obra/superpowers)
`Shell · 总星 328,133 · 今日 +916`

一套面向编码代理的技能框架与软件开发方法论，由可组合的技能和初始指令组成，让代理按照结构化流程完成开发任务。支持 Claude Code、Cursor、Codex、Gemini CLI、GitHub Copilot CLI 等十余种主流编码代理。适合想让 AI 编码代理更规范、更可靠地参与完整开发流程的开发者和团队。

### 3. [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
`Python · 总星 66,859 · 今日 +668`

一个让所有软件对 AI Agent 友好的框架，核心思路是为软件生成 CLI 接口，让代理能够像人操作软件一样调用它们。提供 CLI-Hub 供社区浏览、安装和管理贡献的 CLI，可通过 `pip install cli-anything-hub` 快速上手。适合想让 AI 代理驱动特定软件工具的研究者和开发者，也欢迎社区贡献新的 CLI 适配。

### 4. [jingyaogong/minimind](https://github.com/jingyaogong/minimind)
`Python · 总星 72,146 · 今日 +667`

一个从零开始训练超小语言模型的开源项目，最小版本约 64M 参数，号称个人 GPU 两小时、约三块钱成本即可完成训练。完整覆盖数据清洗、预训练、SFT、LoRA、RLHF（DPO/PPO/GRPO）、Tool Use、模型蒸馏等全链路代码。适合想从底层理解大模型训练全流程的学习者和研究者，项目力求轻量可复现。

### 5. [cursor/plugins](https://github.com/cursor/plugins)
`TypeScript · 总星 19,960 · 今日 +242`

Cursor 编辑器的插件规范与官方插件仓库，每个插件是独立目录并带有自己的 manifest 文件。目前已收录教学、持续学习、团队 CI/代码审查工作流、深度安全审计等插件。适合 Cursor 用户直接安装使用，也适合想为 Cursor 生态开发插件的开发者参考规范。

### 6. [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl)
`TypeScript · 总星 211,502 · 今日 +833`

一套面向 AI 代理的知识基础设施，提供搜索、抓取和访问 550+ 数据提供商的统一 API。支持三种使用方式：本地单二进制运行（可作为 MCP 服务器接入代理）、云端托管服务、以及完全自托管部署。适合需要为 AI 代理提供干净网页数据（markdown 格式）和搜索能力的开发者。

### 7. [nginx/nginx](https://github.com/nginx/nginx)
`C · 总星 33,635 · 今日 +148`

NGINX 开源官方仓库，提供高性能 Web 服务器、负载均衡器、反向代理、API 网关和内容缓存功能。采用 BSD 两条款许可证，企业版和商业支持由 F5 提供。README 标注项目处于 Active 状态，适合 Web 开发者和运维工程师作为官方源码参考和自编译使用。

### 8. [openvinotoolkit/openvino](https://github.com/openvinotoolkit/openvino)
`C++ · 总星 12,916 · 今日 +152`

Intel 开源的深度学习推理优化与部署工具包，支持计算机视觉、语音识别、生成式 AI、大/小语言模型等多种场景的推理加速。提供 PyPI、Conda、npm、Homebrew 等多渠道安装。适合需要在边缘设备或服务器上部署和优化 AI 模型推理性能的开发者和工程师。

### 9. [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
`HTML · 总星 74,333 · 今日 +731`

一个面向 AI 编码代理的图表绘制技能，生成自包含的 HTML + SVG 文件，支持 52 种图表类型，可按品牌风格定制。明确对标 Mermaid，强调无阴影、无"Mermaid slop"的编辑级视觉质量。支持 Claude Code、Codex、GitHub Copilot、Cursor 等多种代理宿主，适合需要让 AI 代理直接产出高质量图表的开发者和内容创作者。

### 10. [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
`Python · 总星 76,244 · 今日 +664`

一个 AI 代理技能，能跨 Reddit、X、YouTube、Hacker News、Polymarket 和网络搜索任意主题，然后综合生成有依据的摘要。结果按点赞、投票甚至真金白银（Polymarket）排序而非编辑筛选，README 称零配置即可运行，Reddit、HN、Polymarket 和 GitHub 开箱即用。适合需要快速了解某主题近 30 天动态的研究者、内容创作者和产品经理。

---
title: "GitHub Trending 每日趋势 · 2026-11-23"
date: 2026-11-23T08:07:26+08:00
draft: false
tags: ["GitHub", "开源", "趋势"]
description: "今日 GitHub 趋势 Top 10 仓库与用途点评"
---

今天的 GitHub Trending 日榜上，“给 AI 代理装上技能和工具”是最突出的主题：从安全测试、软件开发、图表生成到信息检索，开发者们正把代理从“聊天”推向“干活”。与此同时，大模型训练教学、底层推理优化和 Web 基础设施也依然保持着稳定的热度。

### 1. [elementalsouls/Claude-BugHunter](https://github.com/elementalsouls/Claude-BugHunter)
`Python · 总星 17,759 · 今日 +1,716`
这是一个面向 Claude Code 的即插即用技能包，包含 83 个技能、15 个斜杠命令和 681 个公开漏洞报告模式，覆盖 24 个核心漏洞类别及企业身份与基础设施攻击矩阵。安装后，Claude Code 能像资深 bug hunter 一样掌握攻击链模板、VRT 映射等专业知识，适合安全研究员和红队操作者在授权测试中使用。README 明确提到该工具已在授权红队和 bug hunting 实战以及公开训练平台（如 DVWA、OWASP Juice Shop）中经过测试。

### 2. [obra/superpowers](https://github.com/obra/superpowers)
`Shell · 总星 324,151 · 今日 +788`
这是一套面向编码代理的完整软件开发方法论和可组合技能框架，从代理启动那一刻起就介入，确保其按规范使用技能。它支持 Claude Code、Cursor、Codex、Gemini CLI 等十余种主流编码工具，适合想让 AI 编码代理更可控、更系统化地参与开发流程的团队和个人。

### 3. [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
`Python · 总星 62,769 · 今日 +699`
这个项目旨在让所有软件对 AI 代理可用，通过提供 CLI-Hub 来浏览、安装和管理社区构建的 CLI。它能生成 CLI 让代理直接操作 CAD、3D 场景、图表等软件并产出真实成果，适合希望让 AI 代理驱动各类专业软件的开发者和研究者。

### 4. [jingyaogong/minimind](https://github.com/jingyaogong/minimind)
`Python · 总星 68,632 · 今日 +473`
这是一个从 0 开始的大模型训练教学项目，号称用约 3 元成本和 2 小时即可训练出约 64M 规模的超小语言模型。项目开源了极简结构与完整训练链路，覆盖 MoE、数据清洗、预训练、SFT、LoRA、RLHF、Tool Use、模型蒸馏等全过程代码，适合想在个人 GPU 上学习和复现大模型全流程训练原理的开发者和学生。

### 5. [cursor/plugins](https://github.com/cursor/plugins)
`TypeScript · 总星 18,430 · 今日 +294`
这是 Cursor 编辑器的官方插件规范和插件集合，每个插件是仓库根目录下的独立目录，带有自己的 manifest 文件。目前包含教学、持续学习、团队工作流、深度代码审查等插件，适合 Cursor 用户扩展编辑器能力，也适合想为 Cursor 生态开发插件的开发者参考规范。

### 6. [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl)
`TypeScript · 总星 207,012 · 今日 +915`
这是一套为 AI 代理提供知识的搜索与抓取基础设施，通过一个 API 提供搜索、抓取和访问 550+ 数据提供商的能力。它支持本地运行、云端服务和自托管三种模式，本地模式无需数据库即可将网站转为 markdown 并作为 MCP 服务器接入代理，适合需要为 AI 代理提供高质量外部数据的开发者。

### 7. [nginx/nginx](https://github.com/nginx/nginx)
`C · 总星 32,881 · 今日 +163`
这是 NGINX 开源版的官方仓库，提供高性能 Web 服务器、负载均衡器、反向代理、API 网关和内容缓存功能。项目采用 BSD 许大写证，README 标注其处于 Active 稳定状态且正在积极开发，适合需要部署和管理 Web 基础设施的开发者和运维人员。

### 8. [openvinotoolkit/openvino](https://github.com/openvinotoolkit/openvino)
`C++ · 总星 12,089 · 今日 +158`
这是 Intel 开源的深度学习模型优化和部署工具包，支持计算机视觉、语音识别、生成式 AI 和自然语言处理等多种任务的推理加速。它提供 PyPI、Conda、NPM、brew 等多渠道安装方式，适合需要在边缘设备或生产环境中高效部署 AI 模型的开发者。

### 9. [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
`HTML · 总星 70,284 · 今日 +518`
这是一个面向 Claude Code、Codex、Copilot 等编码代理的画图技能，能生成自包含的 HTML+SVG 图表文件，支持 51 种图表类型。它强调无阴影、无 Mermaid 粗制图，可按品牌风格输出，适合需要用 AI 代理快速生成高质量图表的开发者和内容创作者。

### 10. [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
`Python · 总星 72,697 · 今日 +668`
这是一个 AI 代理技能，能跨 Reddit、X、YouTube、HN、Polymarket 和网页研究任意主题，并合成有依据的总结。README 称其按点赞、投票和真金白银（如 Polymarket）排序而非编辑挑选，Reddit、HN、Polymarket 和 GitHub 开箱即用，适合需要快速了解某主题近 30 天动态的研究者、产品经理和内容创作者。

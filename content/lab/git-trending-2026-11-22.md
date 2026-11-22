---
title: "GitHub Trending 每日趋势 · 2026-11-22"
date: 2026-11-22T11:48:18+08:00
draft: false
tags: ["GitHub", "开源", "趋势"]
description: "今日 GitHub 趋势 Top 10 仓库与用途点评"
---

今天的 GitHub Trending 日榜几乎被「AI Agent 技能包」和「编码代理方法论」承包了：大量项目围绕如何给 Claude Code、Cursor、Codex 等代理挂载特定能力（漏洞挖掘、图表生成、信息检索）展开。与此同时，从零训练小模型、优化推理部署以及经典 Web 基础设施也依然占据稳定席位。

### 1. [elementalsouls/Claude-BugHunter](https://github.com/elementalsouls/Claude-BugHunter)
`Python · 总星 16,237 · 今日 +1,803`
这是一个面向 Claude Code 的即插即用技能包，内置 83 个技能、15 个斜杠命令和 681 个公开漏洞报告模式，覆盖 24 个核心漏洞类别以及企业身份与基础设施攻击矩阵。安装后能让 Claude Code 表现得像资深 bug hunting 研究员或红队操作员，熟悉攻击技术、链模板和 VRT 映射。适合安全研究员、红队操作员和 bug bounty 猎人使用。README 明确提到该项目已在授权的红队和 bug hunting 任务以及公开训练平台（DVWA、OWASP Juice Shop 等）上经过实战检验。

### 2. [obra/superpowers](https://github.com/obra/superpowers)
`Shell · 总星 323,805 · 今日 +883`
这是一套面向编码代理的 agentic skills 框架和完整软件开发方法论，由可组合的技能和初始指令构成。它能确保你的编码代理按规范流程工作，支持 Claude Code、Cursor、Codex、Gemini CLI 等十余种宿主环境。适合重度使用 AI 编码代理、希望让代理工作流更规范可控的开发者。

### 3. [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
`Python · 总星 62,147 · 今日 +769`
这个项目旨在让所有软件变成 Agent-Native，提供 CLI-Hub 来浏览、安装和管理社区构建的 CLI。通过 `pip install cli-anything-hub` 安装后，AI 代理可以利用生成的 CLI 操控各类软件，产出 CAD 构建、3D 场景、图表等真实产物。适合想让 AI 代理直接驱动现有软件完成任务的 Agent 构建者和开发者。

### 4. [jingyaogong/minimind](https://github.com/jingyaogong/minimind)
`Python · 总星 68,212 · 今日 +488`
这是一个从零开始训练约 64M 规模小语言模型的开源项目，主打极简与低成本。它声称仅需约 3 块钱成本和 2 小时训练时间，就能在个人 GPU 上完成从数据清洗、预训练、SFT、LoRA、RLHF 到 Tool Use、蒸馏等全链路训练与复现。适合想动手理解大模型完整训练流程的学习者和研究者。

### 5. [cursor/plugins](https://github.com/cursor/plugins)
`TypeScript · 总星 18,141 · 今日 +260`
这是 Cursor 的插件规范和官方插件集合，每个插件是仓库根目录下的独立目录，带有自己的 manifest。目前已提供教学、持续学习、团队工作流（CI、代码审查、发布）、深度安全审查（Thermos）等插件。适合 Cursor 用户以及想为 Cursor 生态开发插件的开发者。

### 6. [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl)
`TypeScript · 总星 206,311 · 今日 +1,006`
这是面向 AI 代理的知识基础设施，提供搜索、抓取和访问 550+ 数据提供商的统一 API。它支持三种使用方式：本地单二进制运行（Firecrawl Local，可作为 MCP 服务器）、托管云服务（Firecrawl Cloud）和完全自托管。适合需要为 AI 代理接入高质量外部知识或网页数据的开发者。

### 7. [nginx/nginx](https://github.com/nginx/nginx)
`C · 总星 32,753 · 今日 +189`
这是 NGINX 官方开源仓库，提供世界最流行的 Web 服务器、高性能负载均衡器、反向代理、API 网关和内容缓存。采用 BSD 2-Clause 许可证，企业版分发和商业支持由 F5 提供。适合需要部署和管理 Web 服务器、反向代理的运维和后端开发者。README 标注项目处于 Active 状态，已达到稳定、可用状态并积极开发。

### 8. [openvinotoolkit/openvino](https://github.com/openvinotoolkit/openvino)
`C++ · 总星 11,956 · 今日 +200`
OpenVINO 是一个用于优化和部署深度学习模型推理的开源工具包。它能提升计算机视觉、语音识别、生成式 AI、NLP 等任务的推理性能，支持大语言模型和小语言模型。适合需要在边缘或生产环境优化和部署 AI 模型的开发者。

### 9. [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
`HTML · 总星 69,852 · 今日 +583`
这是一个 AI 代理技能，能将图表绘制为自包含的 HTML + SVG 文件，支持 51 种图表类型。它强调品牌风格定制，无阴影、无 Mermaid 粗制滥造，支持 Claude Code、Codex、Cursor 等多种宿主。适合需要让 AI 代理产出高质量、可定制图表的开发者和内容创作者。

### 10. [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
`Python · 总星 72,080 · 今日 +560`
这是一个 AI 代理技能，能跨 Reddit、X、YouTube、HN、Polymarket 和网页研究任何话题，然后合成有依据的总结。它由点赞、喜欢和真金白银（如 Polymarket）评分而非编辑筛选，零配置即可使用 Reddit、HN、Polymarket、GitHub 等。适合需要快速获取某话题近期热度趋势和综合摘要的研究者、产品经理和内容创作者。

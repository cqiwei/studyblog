---
title: "GitHub Trending 每日趋势 · 2026-11-26"
date: 2026-11-26T01:39:06+08:00
draft: false
tags: ["GitHub", "开源", "趋势"]
description: "今日 GitHub 趋势 Top 10 仓库与用途点评"
---

今天的 Trending 榜单上，"给 AI 代理装技能"是绝对主旋律——从安全研究、软件开发到图表绘制和信息检索，一批可插拔的 agent skill 包集体冲榜。与此同时，让传统软件"代理化"的中间层（CLI 封装、网页抓取）也在上榜，说明生态正从单点工具向代理原生基础设施演进。

### 1. [elementalsouls/Claude-BugHunter](https://github.com/elementalsouls/Claude-BugHunter)
`Python · 总星 22,622 · 今日 +1,644`
这是一套面向 Claude Code 的即插即用技能包，安装后让 Claude Code 以高级 bug hunting 研究员 / 红队操作员的模式工作，内置 84 个技能、15 个斜杠命令和 681 个已披露报告模式，覆盖 24 个核心漏洞类别，还包含企业身份与基础设施攻击矩阵及 Burp MCP 集成。适合安全研究员、红队操作员和 bug bounty 猎人使用。README 明确提到该工具已在授权的红队和 bug hunting engagement 中经过实战检验，并在 DVWA、OWASP Juice Shop 等公开训练平台上测试过。

### 2. [obra/superpowers](https://github.com/obra/superpowers)
`Shell · 总星 326,414 · 今日 +902`
这是一个面向编码代理的完整软件开发方法论框架，由一组可组合的技能和初始指令构成，确保你的编码代理系统性地使用这些技能。它支持的平台非常广泛，包括 Claude Code、Cursor、GitHub Copilot CLI、Gemini CLI、Codex、Devin、Factory Droid 等十余种主流代理环境。适合想让 AI 编码助手更规范、更可靠地参与完整开发流程的开发者和团队使用。

### 3. [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
`Python · 总星 65,508 · 今日 +1,094`
这个项目的核心理念是"让所有软件对 AI 代理原生友好"——通过为各类软件生成 CLI 接口，弥合 AI 代理与现有软件之间的操作鸿沟。它提供 CLI-Hub 供社区浏览、安装和管理 CLIs，用户也可以提交 PR 贡献新的 CLI。适合需要让 AI 代理操作 CAD、3D 建模、图表等桌面软件或服务的开发者和自动化场景使用。

### 4. [jingyaogong/minimind](https://github.com/jingyaogong/minimind)
`Python · 总星 70,848 · 今日 +828`
这是一个从零开始训练超小语言模型（约 64M 参数）的完整开源项目，号称仅需约 3 块钱成本和 2 小时训练时间即可跑通。项目覆盖了 MoE、数据清洗、预训练、SFT、LoRA、RLHF（DPO/PPO/GRPO）、Tool Use、模型蒸馏等全链路代码，主线最小版本体积约为 GPT-3 的 1/2700。适合想亲手走一遍 LLM 训练全流程、理解每个环节原理的个人开发者和学习者，普通个人 GPU 即可复现。

### 5. [cursor/plugins](https://github.com/cursor/plugins)
`TypeScript · 总星 19,483 · 今日 +408`
这是 Cursor 编辑器的官方插件规范和插件集合，每个插件是仓库根目录下的独立目录，带有自己的 `plugin.json` 清单。目前已收录教学技能映射、持续学习记忆更新、团队 CI/代码审查工作流、深度安全审计（Thermos）等插件。适合 Cursor 用户扩展编辑器能力，也适合想为 Cursor 生态开发插件的开发者参考规范。

### 6. [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl)
`TypeScript · 总星 209,769 · 今日 +1,131`
这是一套面向 AI 代理的知识基础设施，提供搜索、抓取和访问 550+ 数据提供商的统一 API。它支持三种使用方式：Firecrawl Local（本地单二进制运行，将网站转为干净 Markdown 并作为 MCP 服务器接入代理）、Firecrawl Cloud（托管服务，无需自行运行即可大规模使用）、以及完全自托管部署。适合需要为 AI 代理或 RAG 系统提供高质量网页数据的开发者。

### 7. [nginx/nginx](https://github.com/nginx/nginx)
`C · 总星 33,327 · 今日 +174`
这是 NGINX 开源版的官方仓库，作为全球最流行的 Web 服务器，同时可用作高性能负载均衡器、反向代理、API 网关和内容缓存。采用简化的 BSD 类许可证，F5 提供企业发行版和商业支持。README 标注项目状态为 Active——已达到稳定可用状态并持续开发中。适合所有需要 Web 服务、反向代理或 API 网关的后端开发者和运维人员。

### 8. [openvinotoolkit/openvino](https://github.com/openvinotoolkit/openvino)
`C++ · 总星 12,605 · 今日 +188`
OpenVINO 是 Intel 开源的深度学习模型优化与部署工具包，支持计算机视觉、语音识别、生成式 AI、大/小语言模型等多种任务的推理加速。它提供 PyPI、NPM、Anaconda、Homebrew 等多渠道安装，方便在不同平台集成。适合需要在边缘设备或生产环境中优化和部署 AI 推理性能的开发者和工程师。

### 9. [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
`HTML · 总星 72,787 · 今日 +1,133`
这是一个 AI 代理技能，能让 Claude Code、Codex、Cursor、GitHub Copilot 等代理直接绘制图表，输出为自包含的 HTML + SVG 文件，支持 52 种图表类型并可适配品牌风格。项目明确标榜"No Mermaid slop"——不走 Mermaid 那种粗糙渲染路线，而是产出编辑级质量的图表。适合需要让 AI 代理生成高质量架构图、流程图等可视化内容的开发者和团队。

### 10. [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
`Python · 总星 74,931 · 今日 +950`
这是一个 AI 代理搜索技能，能跨 Reddit、X、YouTube、Hacker News、Polymarket 和整个 Web 对任意主题进行调研，然后综合生成有依据的摘要。它的特色是按点赞、投票甚至真金白银（Polymarket 预测市场）来排序信号，而非依赖编辑筛选。适合需要快速了解某话题近 30 天社区动态和热度趋势的研究者、产品经理和开发者。README 提到 Reddit、HN、Polymarket、GitHub 等数据源零配置即可使用，X、YouTube 等需运行一次后通过设置向导解锁。

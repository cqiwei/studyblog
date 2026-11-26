---
title: "GitHub Trending 每日趋势 · 2026-11-27"
date: 2026-11-27T01:38:24+08:00
draft: false
tags: ["GitHub", "开源", "趋势"]
description: "今日 GitHub 趋势 Top 10 仓库与用途点评"
---

今日榜单几乎被 AI Agent 生态强势霸屏：从 Claude Code、Cursor 等编程 Agent 的技能包、插件规范，到让任意软件对 Agent 友好的 CLI 桥接，再到给 Agent 供能的搜索与抓取基础设施——Agent 正在长出完整的工具箱和手脚。与此同时，自研小模型训练链路和推理优化工具包也持续受到关注，说明底层能力建设热度不减。

### 1. [elementalsouls/Claude-BugHunter](https://github.com/elementalsouls/Claude-BugHunter)
`Python · 总星 24,194 · 今日 +1,600`
这是给 Claude Code 用的"一键变身安全研究员"技能包，内置 85 个技能、16 个 slash 命令和 681 个公开漏洞报告模式，覆盖 24 个核心漏洞类别，还附带企业身份与基础设施攻击矩阵。装上之后，Claude Code 不再只是聊天机器人，而是能像资深 bug-hunting 研究员一样知道攻击链模板、VRT 映射和平台 CVE 链。适合安全研究员、红队操作员和 bug bounty 猎人使用。README 明确提到该项目已在授权的红队和 bug-hunting 实战中经过检验，也覆盖了 DVWA、OWASP Juice Shop 等公开训练平台。

### 2. [obra/superpowers](https://github.com/obra/superpowers)
`Shell · 总星 327,263 · 今日 +853`
这是一套面向编码 Agent 的完整软件开发方法论，由可组合的技能和初始指令构成，确保 Agent 按照规范流程工作。它支持 Claude Code、Cursor、Codex、Gemini CLI、GitHub Copilot CLI、Devin CLI 等十余种 Agent 宿主，兼容性非常广。适合重度依赖 AI 编程 Agent 的个人开发者和团队，用来统一不同工具下的开发工作流和出错处理流程。

### 3. [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
`Python · 总星 66,202 · 今日 +744`
这个项目的核心目标是"让所有软件对 Agent 原生友好"——通过为各类软件生成 CLI 接口，让 AI Agent 能够像人一样操作 CAD、3D 建模、图表生成等工具并产出真实产物。用户可以通过 `pip install cli-anything-hub` 安装 CLI-Hub 来浏览、安装和管理社区构建的 CLI，也可以提交 PR 贡献自己的 CLI。适合想让 AI Agent 操控更多软件工具的 Agent 开发者和研究者。

### 4. [jingyaogong/minimind](https://github.com/jingyaogong/minimind)
`Python · 总星 71,538 · 今日 +701`
这是一个"大道至简"的开源项目，让你用约 3 块钱成本和 2 小时训练时间，在个人 GPU 上从零训练出约 64M 规模的超小语言模型。项目开源了完整的训练链路，覆盖数据清洗、预训练、SFT、LoRA、RLHF（DPO/PPO/GRPO/CISPO）、Tool Use、Agentic RL 和模型蒸馏等全过程代码。适合想从零理解大模型训练全链路的学习者和研究者，主线最小版本体积约为 GPT-3 的 1/2700，普通个人 GPU 即可快速复现。

### 5. [cursor/plugins](https://github.com/cursor/plugins)
`TypeScript · 总星 19,725 · 今日 +268`
这是 Cursor 的官方插件规范和插件集合，每个插件是仓库根目录下的独立目录，带有自己的 `.cursor-plugin/plugin.json` manifest。目前已收录 Teaching（技能映射与学习复盘）、Continual Learning（增量记忆更新）、Cursor Team Kit（团队 CI/代码审查工作流）、Thermos（深度安全与正确性审计）等插件。适合 Cursor 用户直接使用，也适合想为 Cursor 生态开发插件的开发者参考标准规范。

### 6. [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl)
`TypeScript · 总星 210,724 · 今日 +1,042`
这是让 AI Agent 更聪明的"知识基础设施"，提供搜索、抓取和 550+ 数据提供商的统一 API。它有三种使用方式：Firecrawl Local（本地单二进制，将网站转为 markdown，作为 MCP 服务器接入 Agent）、Firecrawl Cloud（托管服务，无需自建即可大规模搜索和访问 Alexandria 数据源）、以及完全自托管部署。适合需要为 AI Agent 提供网页抓取和知识获取能力的开发者，灵活性较高。

### 7. [nginx/nginx](https://github.com/nginx/nginx)
`C · 总星 33,484 · 今日 +150`
这是 NGINX 开源官方仓库，世界最流行的 Web 服务器，同时也是高性能负载均衡器、反向代理、API 网关和内容缓存。采用 BSD 2-Clause 许可证，企业版和商业支持由 F5 提供。适合运维工程师、后端开发者和系统架构师使用。README 标注项目状态为 Active，已达到稳定可用状态并持续开发中。

### 8. [openvinotoolkit/openvino](https://github.com/openvinotoolkit/openvino)
`C++ · 总星 12,775 · 今日 +176`
这是 Intel 开源的深度学习模型优化与部署工具包，能提升计算机视觉、语音识别、生成式 AI、NLP（含大小语言模型）等任务的推理性能。支持通过 PyPI、NPM、Anaconda、brew 等多种渠道安装，覆盖 Python、Node.js 等多种语言绑定。适合需要在边缘设备或生产环境中部署和优化 AI 模型的开发者，生态较为成熟。

### 9. [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
`HTML · 总星 73,685 · 今日 +951`
这是一个面向 Claude Code、Codex、Copilot、Cursor 等多种 Agent 的图表设计技能，支持 52 种图表类型，输出为自包含的 HTML + SVG 文件。README 明确打出"No shadows. No Mermaid slop."的旗号，追求编辑级品质而非粗糙生成物，图表可带品牌风格。适合需要 AI Agent 产出高质量技术图表的开发者、产品经理和技术写作者。

### 10. [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
`Python · 总星 75,597 · 今日 +755`
这是一个 AI Agent 技能，能跨 Reddit、X、YouTube、HN、Polymarket 和网页研究任意主题，然后合成有依据的摘要。它的特色是用点赞、投票甚至真金白银（如 Polymarket 预测市场）等信号来给内容评分，而非依赖编辑挑选。Reddit、HN、Polymarket、GitHub 等数据源零配置即可使用，运行一次后设置向导会解锁 X、YouTube、TikTok、arXiv 等更多来源。适合需要快速了解某主题近 30 天动态的研究者、产品经理和投资人。

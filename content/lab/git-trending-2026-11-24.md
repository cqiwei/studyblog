---
title: "GitHub Trending 每日趋势 · 2026-11-24"
date: 2026-11-24T01:40:20+08:00
draft: false
tags: ["GitHub", "开源", "趋势"]
description: "今日 GitHub 趋势 Top 10 仓库与用途点评"
---

今天的榜单几乎被"AI agent 技能/插件"生态刷屏——从安全测试、图表绘制到主题研究，大量项目都在为 Claude Code、Cursor 等编码助手打造可即插即用的能力包。与此同时，让软件对 agent 更友好、让个人也能从零训练模型的基础设施项目也持续受到关注。

### 1. [elementalsouls/Claude-BugHunter](https://github.com/elementalsouls/Claude-BugHunter)
`Python · 总星 19,303 · 今日 +2,037`
这是一套面向 Claude Code 的 bug hunting 与红队测试技能包，包含 80 多个技能、15 个 slash 命令和 681 个已披露漏洞报告模式，覆盖 24 个核心漏洞类别及企业身份与基础设施攻击矩阵。安装后 Claude Code 可像资深安全研究员一样工作，知道攻击链模板、VRT 映射和平台 CVE 链。适合 bug bounty 猎人、红队操作员和安全研究员使用；README 明确提到已在授权红队和 bug hunting 实战以及 DVWA、OWASP Juice Shop 等公开训练平台上验证过。

### 2. [obra/superpowers](https://github.com/obra/superpowers)
`Shell · 总星 324,842 · 今日 +838`
这是一个面向编码 agent 的完整软件开发方法论与可组合技能框架，通过一套初始指令确保 agent 正确使用这些技能。支持 Claude Code、Cursor、Codex、Gemini CLI、GitHub Copilot CLI 等十余种 agent 工具。适合想让 AI 编码助手更规范、更可靠地参与完整开发流程的开发者和团队使用。

### 3. [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
`Python · 总星 63,400 · 今日 +783`
这个项目的核心理念是"让所有软件变成 Agent-Native"——当未来的软件用户从人变成 AI agent 时，需要 CLI 作为桥梁。通过 `pip install cli-anything-hub` 即可浏览、安装和管理社区构建的 CLI 工具，让 agent 能够操作 CAD、3D 场景、图表等各类软件产出真实成果。适合想让 AI agent 操控更多桌面软件和服务的开发者，也欢迎社区贡献新的 CLI。

### 4. [jingyaogong/minimind](https://github.com/jingyaogong/minimind)
`Python · 总星 69,342 · 今日 +828`
这是一个从零开始训练约 64M 参数小语言模型的极简开源项目，号称仅需约 3 块钱成本和 2 小时训练时间，最小版本体积约为 GPT-3 的 1/2700。项目覆盖 MoE、数据清洗、预训练、SFT、LoRA、RLHF（DPO/PPO/GRPO）、Tool Use、模型蒸馏等完整训练链路代码。适合想在个人 GPU 上亲手跑通大模型全流程训练的学习者、学生和独立开发者。

### 5. [cursor/plugins](https://github.com/cursor/plugins)
`TypeScript · 总星 18,741 · 今日 +395`
这是 Cursor 编辑器的官方插件规范与插件集合，每个插件是仓库根目录下一个独立目录，带 `.cursor-plugin/plugin.json` 清单。目前已收录教学技能映射、持续学习记忆、团队 CI/代码审查工作流、深度安全审计等多种插件。适合 Cursor 用户直接安装使用，也适合想为 Cursor 生态开发插件的开发者参考规范。

### 6. [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl)
`TypeScript · 总星 207,663 · 今日 +920`
Firecrawl 是面向 AI agent 的知识基础设施，提供搜索、抓取和访问 550+ 数据提供商的统一 API。支持三种使用方式：本地单二进制运行（无需数据库/队列，可作为 MCP server 接入 agent）、云端托管服务、以及完全自托管部署。适合需要让 AI agent 获取干净网页内容（转为 markdown）或结构化数据的开发者。

### 7. [nginx/nginx](https://github.com/nginx/nginx)
`C · 总星 33,013 · 今日 +174`
这是 NGINX 开源版的官方仓库，提供高性能 Web 服务器、负载均衡器、反向代理、API 网关和内容缓存功能。采用 BSD 2-Clause 许可证，README 标注项目处于 Active 状态且稳定可用。适合需要部署和管理 Web 服务、反向代理和 API 网关的运维工程师和后端开发者，企业版支持和培训由 F5 提供。

### 8. [openvinotoolkit/openvino](https://github.com/openvinotoolkit/openvino)
`C++ · 总星 12,239 · 今日 +183`
OpenVINO 是 Intel 开源的深度学习推理优化与部署工具包，支持计算机视觉、语音识别、生成式 AI、大/小语言模型等多种任务的推理加速。可通过 PyPI、Conda、npm、Homebrew 等多渠道安装。适合需要在 CPU 或边缘设备上优化和部署 AI 模型、追求推理性能的开发者和工程师。

### 9. [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
`HTML · 总星 70,807 · 今日 +624`
这是一个 AI agent 技能，能用自包含的 HTML + SVG 文件绘制 52 种图表类型，支持品牌风格定制，明确标榜"No Mermaid slop"——不走 Mermaid 那套渲染路线。兼容 Claude Code、Codex、GitHub Copilot、Cursor、Factory Droid 等多种 agent 宿主。适合需要让 AI agent 直接产出可编辑、可嵌入的专业图表的开发者和内容创作者。

### 10. [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
`Python · 总星 73,283 · 今日 +790`
这是一个 AI agent 搜索技能，能跨 Reddit、X、YouTube、Hacker News、Polymarket 和网页研究任意主题，然后合成有依据的摘要。其排序依据是点赞、投票甚至真金白银（Polymarket 预测市场）等真实信号而非编辑筛选。适合需要快速了解某主题近 30 天动态趋势的研究者、产品经理和技术决策者；Reddit、HN、Polymarket、GitHub 等数据源零配置即可使用。

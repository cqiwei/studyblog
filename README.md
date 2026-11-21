# 静态博客上线手册（Hugo + Nginx + HTTPS + 一键部署）

这套东西的目标：**在本地写 Markdown，一条命令发到 VPS，网站几秒钟更新**。服务器上不跑 PHP、不跑数据库，1 核 1G 绰绰有余。

```
本地 Windows                          服务器 (Ubuntu 22.04/24.04)
┌─────────────────┐   tar.gz + ssh   ┌──────────────────────────────┐
│ content/*.md    │ ───────────────► │ /var/www/blog/releases/<时间戳>/ │
│ hugo build      │                  │ /var/www/blog/current ──┐      │
│ public/  ───────┘                  │ Nginx 读 current ◄──────┘      │
└─────────────────┘                  └──────────────────────────────┘
```

每次部署都会新建一个 `releases/<时间戳>/` 目录，然后把 `current` 这个软链接指过去。**切换是原子的，回滚就是改一下链接**。

---

## 目录结构

```
blog/
├── hugo.toml                 站点配置（改标题、域名、作者）
├── content/
│   ├── about.md              「关于」页
│   └── posts/                文章，一篇一个 .md
├── layouts/                  模板（已写好，一般不用动）
├── assets/css/main.css       样式（想改配色改这里）
├── .tools/hugo.exe           本地构建用的 Hugo（已下载好）
├── .github/workflows/        GitHub Actions 自动部署（可选）
└── deploy/
    ├── nginx/blog.conf       Nginx 站点配置模板
    └── scripts/
        ├── bootstrap-server.sh   服务器一次性初始化
        ├── remote-release.sh     服务器端「切换版本」脚本
        └── deploy.ps1            本地一键部署
```

---

## 前置条件

- 一台 Ubuntu 22.04 / 24.04 的 VPS，能 SSH 登录，有 root 或 sudo
- 一个域名，能改 DNS 解析
- Windows 上已经能 `ssh`、`scp`（系统自带 OpenSSH，你的机器里已有）

---

## 第 0 步：本地先跑起来

```powershell
cd D:\AI_Project\blog
.\.tools\hugo.exe server -D
```

打开 http://localhost:1313 看效果。改 `content/posts/hello-world.md` 里的文字，页面会自动刷新。

> `.tools\hugo.exe` 是便携版，不污染系统 PATH；想全局用就把它所在目录加进 PATH。

---

## 第 1 步：域名解析

在域名商（Cloudflare / 阿里云 / Namesilo 都行）加两条 A 记录：

| 类型 | 名称 | 值 |
|---|---|---|
| A | `@` | 你的服务器 IP |
| A | `www` | 你的服务器 IP |

**先等解析生效再做第 2 步**，否则证书签发会失败（Let's Encrypt 要访问 `http://你的域名/.well-known/...`）。

验证：

```powershell
nslookup 你的域名
```

返回的 IP 是你的服务器就对了。

---

## 第 2 步：服务器初始化（只做一次）

**2.1 上传部署目录**

```powershell
scp -r D:\AI_Project\blog\deploy root@你的服务器IP:/root/blog-deploy
```

**2.2 在服务器上执行初始化**

```bash
ssh root@你的服务器IP
bash /root/blog-deploy/scripts/bootstrap-server.sh 你的域名 你的邮箱
```

它会依次完成：装 nginx + certbot → 建 `/var/www/blog` → 装站点配置 → 开 22/80/443 防火墙 → 申请证书并开启 HTTPS 跳转。

看到 `done.` 就成了。验证：

```bash
curl -I https://你的域名/
# 期望：HTTP/2 200（此时还是 404 也正常，因为还没部署内容）
```

**2.3（建议）打个快照**

在 Vultr 控制台给这台机器做个快照，之后折腾坏了 30 秒回滚。

---

## 第 3 步：改配置

编辑 `hugo.toml`，把这几项换成你自己的：

```toml
baseURL = "https://你的域名/"     # 结尾的斜杠不能少
title = "海边小屋"                 # 站点名
[params]
  author = "你的名字"
  description = "一句话介绍"
```

⚠️ `baseURL` 写错的典型症状：CSS 加载不出来、页面没样式。部署后先按 F12 看有没有 404 的 css 请求。

---

## 第 4 步：首次部署

```powershell
cd D:\AI_Project\blog
.\deploy\scripts\deploy.ps1 -Target root@你的服务器IP
```

第一次连这台机器，先手动 `ssh root@你的服务器IP` 一次，把 host key 接受了，否则 scp 会卡在 yes/no 提问上。

脚本做的事：构建 → 打包 → scp 上传 → 远端解压到新 release → 切换软链 → `nginx -t` → reload → 只保留最近 5 个版本。

看到 `OK release 20261121-101500 is live` 就上线了。

如果提示 `无法加载文件 ... 因为在此系统上禁止运行脚本`：

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\scripts\deploy.ps1 -Target root@你的服务器IP
```

---

## 第 5 步：日常写作

```powershell
# 1. 新建一篇（草稿状态）
.\.tools\hugo.exe new content posts/my-second-post.md

# 2. 本地预览（含草稿）
.\.tools\hugo.exe server -D

# 3. 写完把 front matter 里的 draft 改成 false

# 4. 发布
.\deploy\scripts\deploy.ps1 -Target root@你的服务器IP
```

想跳过重新构建（比如只改了 public 里的东西）：

```powershell
.\deploy\scripts\deploy.ps1 -Target root@你的服务器IP -SkipBuild
```

---

## 可选：GitHub Actions 自动部署

推到 GitHub 后，每次 `git push` 自动上线，不用开电脑。

1. 本地仓库推上去：

```powershell
cd D:\AI_Project\blog
git init
git add .
git commit -m "init blog"
git branch -M main
git remote add origin git@github.com:你的用户名/仓库名.git
git push -u origin main
```

2. 生成一把专用密钥（在服务器上执行，**不要设密码**）：

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/gh_deploy -N ""
cat ~/.ssh/gh_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/gh_deploy          # 复制这一整段，等下贴到 GitHub
```

3. GitHub 仓库 → Settings → Secrets and variables → Actions，加四个 secret：

| Name | Value |
|---|---|
| `SSH_HOST` | 服务器 IP |
| `SSH_USER` | `root`（或你的部署用户） |
| `SSH_PORT` | `22`（改过端口就填实际值） |
| `SSH_KEY` | 上一步 `cat` 出来的私钥全文（含 `-----BEGIN...` 和 `-----END...`） |

4. 提交并推送，在仓库的 Actions 标签页看进度。

> 私钥只存在 GitHub Secrets 里，不会进仓库。**别把私钥写进任何文件再 commit。**

---

## 和代理共存：443 端口冲突

这是最容易踩的坑——**Nginx 和你的代理都想用 443**，先启动的那个会占住端口。

两种解法：

**方案 A（推荐先这样，五分钟搞定）**：博客占 443，代理换到 8443。

- 改代理服务端配置的监听端口为 8443，客户端同步改
- 服务器防火墙放行 8443：`ufw allow 8443/tcp`
- 博客继续用标准 443，浏览器访问不了才奇怪

**方案 B（进阶，以后再折腾）**：Xray 的 VLESS + fallback，让代理和网站共用 443，按 SNI 分流，伪装性最好，但配置复杂、排错麻烦。等博客稳定了再考虑。

⚠️ 如果代理用了**非 22 的 SSH 端口**，在跑 `bootstrap-server.sh` 之前先把脚本里的 `ufw allow OpenSSH` 改成你的实际端口，否则防火墙一开就把自己关在门外。

---

## 回滚

```bash
# 看有哪些版本
ls -1 /var/www/blog/releases/

# 切回上一个
ln -sfn /var/www/blog/releases/20261120-213000 /var/www/blog/current
systemctl reload nginx
```

因为每个版本是独立目录，回滚不需要重新上传任何东西。

---

## 备份

静态站没有数据库，**Git 仓库本身就是备份**（`content/` 和配置都在里面）。额外想保险的话：

```bash
# 服务器上打包站点目录，下载回本地
tar -czf /tmp/blog-backup-$(date +%F).tar.gz -C /var/www/blog/releases .
```

真正需要备份的其实是**文章源文件**，所以：把 `content/` 推到 GitHub 就是最好的备份。

---

## 排错速查

| 现象 | 原因 | 处理 |
|---|---|---|
| 页面没样式 | `baseURL` 写错 / 资源 404 | 改 `hugo.toml` 重新部署，F12 看 Network |
| 502 / 403 | `/var/www/blog/current` 指向空目录 | `ls -l /var/www/blog/current` 确认链接 |
| 证书签发失败 | 解析还没生效，或 80 端口被墙/被占 | `nslookup` 确认；`curl -I http://域名/` |
| 改了文章线上没变 | 浏览器缓存 / 部署没成功 | 强制刷新；看 deploy 输出有没有 `OK` |
| `nginx -t` 报错 | 配置文件语法 | `nginx -t` 的输出会指到具体行号 |
| scp 卡住不动 | 首次连接在等 host key | 先手动 `ssh` 一次 |
| 部署后 404 | 文章 `draft: true` | 改成 `false` 再构建 |
| 页面中文乱码 | 编辑器存成了 GBK | 一律存 UTF-8（无 BOM） |

---

## 之后想加什么

- **工具页**：在 `content/tools/` 下新建页面，`layouts/` 里加一个 `single` 模板即可，纯前端 JS 就能跑
- **图片加速**：图片传对象存储（Backblaze B2 / 阿里云 OSS），Markdown 里直接写外链
- **访问统计**：Cloudflare Web Analytics 或 Umami，免 Cookie、不拖慢页面
- **评论**：Giscus（基于 GitHub Discussions），纯静态站也能有评论
- **CDN**：域名托管到 Cloudflare，开小云朵，国内访问会稳一些

---

需要我把「页面里加一个工具页」或者「换成 Cloudflare DNS + CDN」也写出来，随时说。
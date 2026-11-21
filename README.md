# 静态博客上线手册（Hugo + Nginx + HTTPS + 一键部署）

这套东西的目标：**在本地写 Markdown，一条命令发到 VPS，网站几秒钟更新**。服务器上不跑 PHP、不跑数据库，1 核 1G 绰绰有余。

> 当前部署实例：**https://aiqivy.com** —— Vultr 203.0.113.10，CentOS Stream 10 + nginx 1.26.3 + Let's Encrypt（certbot-renew.timer 自动续期）。

```
本地 Windows                          服务器 (Ubuntu / CentOS / RHEL 系)
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

- 一台 VPS（Ubuntu 22.04/24.04，或 CentOS Stream / RHEL / Alma / Rocky 系），能 SSH 登录，有 root 或 sudo
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

脚本自己识别发行版，不用你改：

| | Debian / Ubuntu | CentOS / RHEL / Alma / Rocky |
|---|---|---|
| 包管理 | `apt` | `dnf`（缺 `certbot-nginx` 会自动装 EPEL） |
| 站点配置 | `/etc/nginx/sites-available/blog` | `/etc/nginx/conf.d/blog.conf` |
| 运行用户 | `www-data` | `nginx` |
| 防火墙 | `ufw` | `firewalld`（`--add-service=http/https`） |

**如果 DNS 还没指过来**，别急着申请证书（Let's Encrypt 会连不上，白等一轮失败）：

```bash
bash /root/blog-deploy/scripts/bootstrap-server.sh 你的域名 --skip-cert
```

解析生效后再补一条：

```bash
certbot --nginx -d 你的域名 -d www.你的域名 --agree-tos -m 你的邮箱 --redirect
```

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

如果你的私钥不是默认的、或者主机指纹没进 `known_hosts`（新机器第一次连就是这么回事），多给两个参数：

```powershell
.\deploy\scripts\deploy.ps1 -Target root@你的服务器IP `
  -Identity "$env:USERPROFILE\.ssh\id_ed25519" `
  -KnownHosts "D:\AI_Project\blog\.ssh_known_hosts"
```

也可以把它们设成环境变量 `BLOG_IDENTITY` / `BLOG_KNOWN_HOSTS`，以后就不用每次带。

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
- 服务器防火墙放行 8443：`ufw allow 8443/tcp`（CentOS 上是 `firewall-cmd --permanent --add-port=8443/tcp && firewall-cmd --reload`）
- 博客继续用标准 443，浏览器访问不了才奇怪

**方案 B（进阶，以后再折腾）**：Xray 的 VLESS + fallback，让代理和网站共用 443，按 SNI 分流，伪装性最好，但配置复杂、排错麻烦。等博客稳定了再考虑。

⚠️ 如果代理用了**非 22 的 SSH 端口**，在跑 `bootstrap-server.sh` 之前先把脚本里的 `ufw allow OpenSSH`（CentOS 上是 `firewall-cmd` 那段）改成你的实际端口，否则防火墙一开就把自己关在门外。

---

## 走 Cloudflare（橙色云朵）

这一步是可选的。好处：隐藏源站 IP、免费 DDoS 防护、静态资源全球缓存。代价：多一跳，国内访问可能反而慢一点（取决于被分到哪个边缘节点）。

### 1. 顺序很重要：先改 SSL 模式，再开云朵

DNS → Records → 把 A 记录的云朵点亮之前，先确认 **SSL/TLS → Overview → Full (strict)**。

原因：源站 Nginx 会把 80 全部 301 到 443。如果 CF 是 `Flexible` 模式（CF 用 HTTP 回源），回源请求被源站 301 到 HTTPS，浏览器又被 CF 拉回 HTTP —— **无限重定向**。`Full (strict)` 下 CF 用 HTTPS 回源并校验源站证书，正好匹配 Let's Encrypt。

### 2. HTML 默认不缓存，得自己加规则

云朵打开后你会发现 HTML 还是 `cf-cache-status: DYNAMIC`，也就是**每次访问都回源**，首字节没变快。静态站可以让边缘把 HTML 也缓存起来：

Cache → Cache Rules → 新建一条（本项目实际用的配置）：

| 项 | 值 |
|---|---|
| 匹配 | `http.request.method eq "GET"` 且路径是 `/`、以 `/` 结尾、`*.html`、`/index.xml`、`/sitemap.xml`、`/robots.txt` |
| Cache eligibility | Cache everything |
| Edge TTL | Override origin，3600 秒 |
| Browser TTL | Bypass（避免浏览器缓存住旧页面） |

对应 API 是 `PUT /zones/<zone>/rulesets/phases/http_request_cache_settings/entrypoint`，规则体：

```json
{
  "action": "set_cache_settings",
  "action_parameters": {
    "cache": true,
    "edge_ttl": { "mode": "override_origin", "default": 3600 },
    "browser_ttl": { "mode": "bypass" }
  }
}
```

### 3. 部署后必须清缓存

HTML 被边缘缓存 1 小时，意味着**发新文章后 1 小时内老访客看不到**。所以部署脚本最后加了一步 purge `purge-cache.py`，只要设了环境变量就会自动执行：

```powershell
setx CLOUDFLARE_API_TOKEN "你的token"     # 需要 Zone -> Cache Purge -> Purge
setx CLOUDFLARE_ZONE_ID  "zone_id"       # 可选，不设就按 CLOUDFLARE_ZONE_NAME 查
setx CLOUDFLARE_ZONE_NAME "aiqivy.com"   # 可选，默认就是这个
```

没设 token 就跳过（等价于 `-SkipPurge`），手动清：`python deploy\scripts\purge-cache.py`。

不想每次 `setx` 的话，把变量写进 `.deploy\cf.env`（已在 `.gitignore` 里，不会进仓库），`deploy.ps1` 启动时会自动读取：

```
CLOUDFLARE_API_TOKEN=你的token
BLOG_IDENTITY=C:\Users\123\.ssh\id_ed25519
BLOG_KNOWN_HOSTS=D:\AI_Project\blog\.ssh_known_hosts
```

已有的环境变量优先级更高，想临时换 token 直接 `$env:CLOUDFLARE_API_TOKEN=...` 覆盖即可；也可以用 `-EnvFile 别的路径` 指定。

### 4. 回退

DNS 里把两条 A 记录的云朵点灰即可，秒级生效。SSL 模式保持 `Full (strict)` 不影响直连。缓存规则留着也没事（不代理时它不起作用）。

### 5. 开了云朵之后的副作用

- **访问日志里全是 Cloudflare 的 IP**。已用 `ngx_http_realip_module` + 定期同步 CF 网段解决，见下面第 6 节。`log_format` 里原来尾部还钉了一个 `$http_x_forwarded_for`，会让同一个 IP 在一行里出现两次，已去掉（`/etc/nginx/nginx.conf:18-20`）。
- **证书续期仍能过**：CF 会把 `/.well-known/acme-challenge/` 回源到 80，源站 301 到 443 后 certbot 的 `--nginx` 仍能应答。真出问题就临时把云朵点灰再续。

### 6. 还原真实访客 IP（real_ip）

开了云朵之后，`$remote_addr` 全是 Cloudflare 边缘节点的地址，日志、限流、封禁全都失去意义。CF 会把真实客户端地址放在 `CF-Connecting-IP` 头里，让 nginx 在**且仅在**对端是 CF 网段时信任它：

```nginx
set_real_ip_from 173.245.48.0/20;   # ... 共 22 段（v4 + v6）
real_ip_header CF-Connecting-IP;
real_ip_recursive on;
```

这些网段会变（CF 偶尔增减），所以不要手写死。仓库里带了一个同步脚本 + systemd 定时器：

```bash
# 在服务器上执行
scp deploy/scripts/cf-realip-update.sh root@服务器:/usr/local/bin/
scp deploy/scripts/cf-realip.{service,timer} root@服务器:/etc/systemd/system/
ssh root@服务器 "chmod 755 /usr/local/bin/cf-realip-update.sh && \
  systemctl daemon-reload && \
  /usr/local/bin/cf-realip-update.sh && \
  systemctl enable --now cf-realip.timer"
```

脚本的行为：拉 `https://www.cloudflare.com/ips-v4|ips-v6` → 校验段数（少于 10 段视为异常，拒绝写入）→ 写 `/etc/nginx/conf.d/cloudflare-realip.conf` → `nginx -t` 通过才 reload，失败自动回滚。定时器每天 04:17（±1 小时）跑一次。

验证方法：随便访问一次带唯一 query 的地址，然后看日志里 `$remote_addr` 是不是你自己的 IP：

```bash
curl -s "https://aiqivy.com/?probe=$RANDOM" >/dev/null
tail -n 1 /var/log/nginx/access.log
# 152.163.13.199 - - [21/Nov/2026:02:59:52 +0000] "GET /?probe=12345 HTTP/1.1" 200 1026 "-" "Mozilla/5.0 ..."
```

### 7. 源站只接受 Cloudflare 的流量

光还原 IP 还不够：任何人只要知道 `203.0.113.10`，就能绕过 Cloudflare 直连源站，缓存和防护全部失效。所以把 80/443 也收进白名单。

做法不是一条条写 44 条 rich rule，而是用一个**专门放 CF 网段的 zone**：firewalld 按来源把流量分派到 zone，CF 网段的流量进 `cfweb`（只开 80/443），其余流量落到 `public`（已删掉 http/https）→ 默认 target 是 `default`（拒绝），直接被丢。

```bash
# 一次性：把 http/https 从 public 摘掉（脚本只负责维护 cfweb 的网段）
firewall-cmd --permanent --zone=public --remove-service=http --remove-service=https
firewall-cmd --reload
```

`cf-realip-update.sh` 在写完 nginx 配置后会自动同步 `cfweb` 的 sources（新增/删除都按当前官方列表对齐），zone 不存在时会自己建。想看效果：

```bash
firewall-cmd --zone=cfweb --list-all        # sources 22 段，ports 80/tcp 443/tcp
firewall-cmd --zone=public --list-services  # 应该只剩 cockpit dhcpv6-client ssh
```

验证（从你自己电脑）：直连 IP 应该超时，走域名正常。

```powershell
Test-NetConnection 203.0.113.10 -Port 443   # TcpTestSucceeded : False（超时）
Invoke-WebRequest https://aiqivy.com -UseBasicParsing   # 200
```

⚠️ **副作用**：直连源站调试、或者临时点灰云朵都会连不上。要临时放行自己的 IP：

```bash
firewall-cmd --zone=public --add-rich-rule='rule family="ipv4" source address="你的公网IP/32" port port="443" protocol="tcp" accept'
firewall-cmd --zone=public --remove-rich-rule='rule family="ipv4" source address="你的公网IP/32" port port="443" protocol="tcp" accept'
```

（`public` 里加富规则是临时的，重启 reload 后仍在 permanent 里——不加 `--permanent` 则 `--reload` 后消失。）

⚠️ 证书续期不受影响：Let's Encrypt 的 HTTP-01 校验请求本身就是从 CF 边缘回源的，落在 `cfweb` 白名单内。

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

## 安全加固

服务器初始只给了 root 密码登录，这等于把整个系统交给一个可能被猜中的字符串。目标状态是**只能凭私钥登录**，密码通道彻底关掉。

### 1. 装公钥

```bash
# 本机（Windows）把公钥内容贴进去；没有 key 就先 ssh-keygen -t ed25519
ssh root@服务器IP "mkdir -p /root/.ssh && chmod 700 /root/.ssh && \
  echo 'ssh-ed25519 AAAA...你的公钥' >> /root/.ssh/authorized_keys && \
  chmod 600 /root/.ssh/authorized_keys"
```

**先新开一个窗口验证 `ssh root@服务器IP` 能免密登录，再往下做** —— 否则下一步会把自己锁在外面。

### 2. 关掉密码认证

CentOS / RHEL 上有个坑：`sshd_config` 里 `Include /etc/ssh/sshd_config.d/*.conf` 在第 15 行，而 sshd 对同一关键字**取第一个出现的值**，所以 drop-in 目录里的设置会盖掉主配置文件后面的设置。云镜像自带的 `/etc/ssh/sshd_config.d/50-cloud-init.conf` 往往写着 `PasswordAuthentication yes`，只改主配置**不生效**。

稳妥做法是新建一个排序更靠前的 drop-in：

```bash
cat > /etc/ssh/sshd_config.d/10-hardening.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
PubkeyAuthentication yes
PermitEmptyPasswords no
EOF
chmod 600 /etc/ssh/sshd_config.d/10-hardening.conf
sshd -t && systemctl reload sshd
sshd -T | grep -iE '^(passwordauthentication|permitrootlogin)'
```

`10-` 前缀让它排在 `50-cloud-init.conf` 前面，这样即使 cloud-init 重写了自己的文件，加固依然有效。

### 3. 验证

```bash
# 应成功
ssh root@服务器IP true && echo 密钥OK
# 应报 Permission denied (publickey,...)，列表里没有 password
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password root@服务器IP true
```

改坏了怎么办：控制台/VNC 进去，用备份还原 —— 脚本已把原文件存成 `/root/*.bak.<时间戳>`。

### 4. 还没做的

- **root 密码本身没改过**，如果它曾经出现在聊天记录、截图、剪贴板里，登录通道关了也建议改一次：`passwd`。
- 想要更彻底，可以禁用 root 直接登录、建一个普通用户 + sudo，再把 22 端口换个高位端口（记得同步改 firewalld 规则）。

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
| 跑 `deploy.ps1` 报「字符串缺少终止符」 | PowerShell 5.1 把**无 BOM 的 UTF-8** `.ps1` 当 GBK 读，中文注释/字符串被截断 | 用「UTF-8 with BOM」另存；VSCode 右下角点编码 → Save with Encoding → UTF-8 with BOM |
| 开云朵后浏览器报「重定向次数过多」 | CF SSL 模式是 `Flexible`，和源站 80→443 跳转打架 | SSL/TLS → Overview → 改 `Full (strict)` |
| 开了云朵但访问没变快 | HTML 是 `cf-cache-status: DYNAMIC`（不缓存） | 加 Cache Rule 缓存 HTML，见「走 Cloudflare」一节 |
| 发文章后线上还是旧内容 | 边缘缓存没清 | 设 `CLOUDFLARE_API_TOKEN` 让部署脚本自动 purge，或手动跑 `purge-cache.py` |

---

## 之后想加什么

- **工具页**：在 `content/tools/` 下新建页面，`layouts/` 里加一个 `single` 模板即可，纯前端 JS 就能跑
- **图片加速**：图片传对象存储（Backblaze B2 / 阿里云 OSS），Markdown 里直接写外链
- **访问统计**：Cloudflare Web Analytics 或 Umami，免 Cookie、不拖慢页面
- **评论**：Giscus（基于 GitHub Discussions），纯静态站也能有评论
- **CDN**：域名托管到 Cloudflare，开小云朵，国内访问会稳一些

---

需要我把「页面里加一个工具页」或者「换成 Cloudflare DNS + CDN」也写出来，随时说。
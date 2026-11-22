---
title: "从域名到上线：一个人搭独立博客的完整流程"
date: 2026-11-21T12:00:00+08:00
tags: ["建站", "Hugo", "入门"]
description: "买域名、配 GitHub、写 Hugo、挂 Nginx、签证书、套 Cloudflare——把这条链路从头走一遍，顺便记下我踩过的每一个坑。"
aliases: ["/posts/blog-from-zero/"]
---

这个站是自己搭的：域名在 Cloudflare，代码在 GitHub，页面跑在一台 1 核 1G 的小 VPS 上，发布一条命令。

整套东西拆开看只有四块积木，任何一块都能单独换掉。下面按我第一次搭站的顺序写，命令都是能直接复制跑的，坑也都是真踩过的。

<figure>
  <img src="images/01-dns.gif?v=2" alt="DNS 解析链路：浏览器 → Cloudflare DNS → 源站服务器" width="880" height="440" loading="lazy">
  <figcaption>图 1：一次典型的 DNS 查询。域名只是门牌号，真正干活的是后面那台机器。</figcaption>
</figure>

## 先说成本，免得你中途放弃

| 项目 | 花多少 | 说明 |
| --- | --- | --- |
| 域名 | ¥70–90 / 年 | `.com` 正常价，首年促销的续费往往翻倍 |
| 服务器 | $5 / 月（约 ¥430 / 年） | 1 核 1G 足够跑静态站；也常有人用免费额度 |
| HTTPS 证书 | 0 | Let's Encrypt |
| CDN / DNS | 0 | Cloudflare 免费版够用 |
| 代码托管 | 0 | GitHub 私有仓库免费 |

也就是说，**一年三四百块**就能拥有一个完全属于自己的角落。真正的成本不是钱，是你愿不愿意花两个晚上把它跑通——而这两个晚上，这篇文里已经替你走过一遍了。

## 全景：四块积木

1. **域名**：让世界能叫出你的名字。
2. **代码**：文章和模板，用 Git 管起来。
3. **服务器**：一台 7×24 在线的机器，负责把 HTML 发出去。
4. **证书与加速**：HTTPS，以及一层挡在源站前面的 Cloudflare。

顺序很重要：**先能让域名解析到机器，再谈证书**。反过来做，certbot 会因为验证不到域名而失败。

## 第一步：注册域名，并把它交给 Cloudflare

注册商我推荐两类：

- **Cloudflare Registrar**：按成本价卖，没有续费陷阱，但需要先把域名转进去；
- **NameSilo / Porkbun**：价格透明，注册即用，适合第一次买。

国内厂商也能买，但要实名，服务器在大陆还得备案。**如果你的服务器在境外，访问者也在境外或走 CDN，就不需要备案**——这一点能省掉最麻烦的一环。

买完之后做一件事：**把 DNS 托管到 Cloudflare**。在 Cloudflare 里添加站点，它会给你两个 NS 地址，回注册商把 NS 改过去，等生效（几分钟到几小时）。之后所有的解析、证书、缓存、防攻击都在一个面板里。

然后加两条 A 记录：

```text
类型   名称    内容              代理状态
A      @      你的服务器 IP      仅 DNS（灰云）
A      www    你的服务器 IP      仅 DNS（灰云）
```

**第一次一定先关掉小云朵（灰云）**。橙云会隐藏源站 IP，但也会让 Let's Encrypt 的 HTTP 验证绕一圈；等证书签下来、站点跑通了，再开橙云不迟。

> 我在这里踩过一个很隐蔽的坑：某天站点突然打不开，本机 `nslookup` 却返回了两个地址——Cloudflare 的，还有一条**旧的源站 IP**。原因是路由器的 DNS 缓存没刷新，浏览器挑中了那条直连源站的记录，而源站防火墙只放行 Cloudflare 网段，于是超时。`ipconfig /flushdns` 对本机有效，对上游缓存无效，只能等 TTL 过期。**改了记录后打不开，先怀疑 DNS 缓存，别急着改服务器。**

## 第二步：注册 GitHub，配好 SSH

注册没什么好说的，记得**开两步验证**。真正容易卡住的是 SSH。

```bash
ssh-keygen -t ed25519 -C "you@example.com"
# 一路回车，默认写到 ~/.ssh/id_ed25519
```

然后把 `id_ed25519.pub`（公钥，`.pub` 结尾那个）贴到 GitHub。这里有个概念要分清：

| 加在哪 | 作用范围 | 典型用途 |
| --- | --- | --- |
| Settings → SSH and GPG keys | 你名下所有仓库 | 日常开发 |
| 仓库 → Settings → Deploy keys | 仅这一个仓库 | 只给某台机器推送权限 |

给服务器、CI 用 Deploy key 更安全：泄露了也只影响一个仓库。我第一次就是把 Deploy key 当账号 key 加，`ssh -T` 返回的是 `Hi 用户名/仓库名!` 而不是 `Hi 用户名!`——看到这种返回，说明你加的是仓库级密钥。

验证：

```bash
ssh -T git@github.com
# Hi yourname! You've successfully authenticated...
```

<figure>
  <img src="images/02-git.gif?v=2" alt="本地提交推送到 GitHub 的过程" width="880" height="440" loading="lazy">
  <figcaption>图 2：本地三个提交推送到远端。有了 Git，改坏了随时能回到上一版。</figcaption>
</figure>

**Windows 上的一个坑**：某些受限环境里，Git 自带的 `ssh.exe` 会因为创建不了管道而报 `couldn't create signal pipe, Win32 error 5`，`git push` 直接失败。解决办法是改用系统的 OpenSSH：

```bat
:: .tools\gitsh.bat
"C:\Windows\System32\OpenSSH\ssh.exe" -o BatchMode=yes %*
```

```powershell
$env:GIT_SSH = "D:/path/to/.tools/gitsh.bat"
```

## 第三步：本地把站跑起来

用 Hugo，因为它是单文件二进制，构建一个几百页的站只要几百毫秒。

```bash
# Windows
winget install Hugo.Hugo.Extended
# 或者直接下 release 里的 hugo_extended_*_windows-amd64.zip 解压

hugo new site blog
cd blog
hugo new content posts/hello.md
hugo server -D          # 本地预览，改文件自动刷新
```

`hello.md` 开头的 front matter 是元数据：

```toml
+++
title = "第一篇"
date = 2026-11-21T12:00:00+08:00
tags = ["随笔"]
draft = false
+++
```

> **最容易让人怀疑人生的坑**：`date` 写成了未来的时间。Hugo 默认**不渲染未来文章**，于是你眼睁睁看着 `hugo` 构建成功、页面数却少了一篇。要么把时间改到过去，要么构建时加 `--buildFuture`。

模板可以套主题，也可以自己写。我自己写了一套 `layouts/`：一个 `baseof.html` 加几个 partial，比改别人的主题更好控制——毕竟你要的是"自己的站"，不是"别人主题的样张"。

## 第四步：服务器与目录结构

一台 1 核 1G 的机器足够。位置比配置重要：读者在国内，就选东京、首尔、新加坡；纯自己看，便宜的美国年付机也行。

装 Nginx：

```bash
# Debian/Ubuntu
apt install -y nginx
# CentOS/RHEL 系
dnf install -y nginx
```

目录结构我用了"版本目录 + 软链接"这一套，**这是整套方案里最值钱的设计**：

```text
/var/www/blog/
├── releases/
│   ├── 20261121-101746/
│   └── 20261121-115732/
└── current -> releases/20261121-115732
```

Nginx 只认 `current`，发布时把新版本解压到 `releases/新时间戳`，校验没问题后一条 `ln -sfn` 把软链接指过去，再 `nginx -t && systemctl reload nginx`。

好处有三个：

- **原子切换**：要么全是新版，要么全是旧版，不会出现一半新一半旧；
- **秒级回滚**：把软链接指回上一个目录即可，不用重新构建；
- **留档**：保留最近 5 个版本，出问题随时对比。

对应的 Nginx 配置核心就几行：

```nginx
server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    root /var/www/blog/current;
    index index.html;

    location / {
        try_files $uri $uri/ $uri.html =404;
    }

    location ~* \.(css|js|gif|jpg|png|svg|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }

    add_header Strict-Transport-Security "max-age=15552000" always;
}
```

## 第五步：一条命令发布

本地写一个脚本，做四件事：**构建 → 打包 → 上传 → 远端切换**。

```powershell
# deploy.ps1（节选）
hugo --minify --gc
tar -czf $archive -C public .
scp -P $port $archive "root@$host:/tmp/"
ssh -p $port "root@$host" "bash -s -- $stamp /tmp/$archive" < remote-release.sh
```

远端脚本负责最后两步：

```bash
# remote-release.sh（节选）
mkdir -p /var/www/blog/releases/$STAMP
tar -xzf "$ARCHIVE" -C /var/www/blog/releases/$STAMP
[ -f /var/www/blog/releases/$STAMP/index.html ] || { echo "坏包，放弃"; exit 1; }
ln -sfn /var/www/blog/releases/$STAMP /var/www/blog/current
nginx -t && systemctl reload nginx
ls -1dt /var/www/blog/releases/* | tail -n +6 | xargs rm -rf
```

注意 `[ -f ...index.html ] || exit 1` 这一行：**先验证再切换**。宁可这次发布失败，也不要让线上变成一个只有 404 的空目录。

<figure>
  <img src="images/03-deploy.gif?v=2" alt="终端里执行部署脚本的全过程" width="880" height="440" loading="lazy">
  <figcaption>图 3：从敲下命令到线上更新，十几秒。构建在本地，服务器只负责接收和切换。</figcaption>
</figure>

`tar -C public .` 那个 `.` 很关键——它保证归档里是 `./index.html` 这样的结构，而不是多套一层 `public/` 目录。

## 第六步：HTTPS

证书用 Let's Encrypt，一条命令：

```bash
certbot --nginx -d example.com -d www.example.com \
  --agree-tos -m you@example.com --redirect
```

它会自动改 Nginx 配置、加 301 跳转、装好续期定时器。

几个细节：

- **续期是自动的**，`systemctl list-timers | grep certbot` 能看到下次时间，不用管；
- **`certbot renew --dry-run` 可能"卡住"几分钟**——那是它在随机延迟（日志里写着 `random delay of 421 seconds`），不是坏了；
- 补邮箱：`certbot update_account --email you@example.com --no-eff-email`，证书快过期时才会给你发提醒。

## 第七步：套上 Cloudflare

打开小云朵（橙云）之后，有件事必须做对：**SSL/TLS 模式选 Full (strict)**。选 Flexible 会形成"用户→CF 是 HTTPS，CF→源站是 HTTP"的循环，运气不好就是无限重定向。

橙云还有一个副作用：**源站 IP 暴露在证书的透明日志里，但至少扫描器扫不到端口了**。更进一步，可以让源站只接受 Cloudflare 的流量：

```bash
# 建一个只放行 Cloudflare 网段的 zone
firewall-cmd --permanent --new-zone=cfweb
firewall-cmd --permanent --zone=cfweb --add-port=80/tcp --add-port=443/tcp
firewall-cmd --permanent --zone=cfweb --add-source=173.245.48.0/20
# ……把官方 ips-v4 / ips-v6 全部加进去
firewall-cmd --permanent --zone=public --remove-service=http --remove-service=https
firewall-cmd --reload
```

Cloudflare 的 IP 段会变，所以写个定时任务每天拉一次官方列表同步。做完之后，直连 `你的IP:443` 会超时，只有走 Cloudflare 才通。

还有两件配套小事：

- **真实 IP**：开了橙云后，Nginx 日志里的 `$remote_addr` 全是 Cloudflare 的地址。装 `realip` 模块（发行版自带），配 `set_real_ip_from` + `real_ip_header CF-Connecting-IP`，日志才认得出真人；
- **HTML 默认不缓存**：Cloudflare 把 `.html` 当动态内容，免费版需要自己加一条 Cache Rule（匹配 `GET` 且路径以 `/` 结尾或 `.html`），否则每次回源。

> 顺便提醒：API Token 别贴进聊天记录和截图里。真贴了，去面板吊销重发一个——**Token 的权限只给需要的**（改 DNS、清缓存），不要给全局 key。

## 第八步：日常写作流

真正用起来之后，流程只有三步：

```bash
hugo new content posts/新文章.md   # 1. 新建
hugo server -D                      # 2. 本地预览
./deploy/scripts/deploy.ps1         # 3. 发布
```

图片放在文章同目录的 `images/` 下，Markdown 里写 `![](images/xxx.gif)` 就行。这样每篇文章是一个"包"，迁站时整个目录拷走即可。

备份也不用额外做：**Git 仓库本身就是备份**，服务器挂了重新开一台，克隆、跑一遍初始化脚本、发布一次，十分钟就能回来。

## 踩坑速查表

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 构建成功但少一篇 | `date` 是未来时间 | 改时间或 `--buildFuture` |
| push 报 `couldn't create signal pipe` | Git 自带 ssh 在受限环境起不来 | `GIT_SSH` 指向系统 OpenSSH |
| 站点突然超时，DNS 却"有解析" | 上游 DNS 缓存了旧 IP，直连源站被墙 | 等 TTL 过期；别急着改服务器 |
| certbot 验证失败 | 域名还没解析到这台机器 | 先 A 记录生效，再签证书 |
| `renew --dry-run` 像卡死 | 随机延迟，设计如此 | 等几分钟或看日志 |
| 日志里 IP 重复两行 | `log_format` 里同时打了 `$remote_addr` 和 `$http_x_forwarded_for` | 去掉后者，配合 realip |
| 改了脚本立刻语法报错 | PowerShell 5.1 把无 BOM 的 UTF-8 当 GBK | 存成 UTF-8 with BOM |
| 部署成功但页面没变 | Cloudflare 边缘缓存 | 加 Cache Rule 或部署后 purge |

## 最后

这套方案最大的好处不是"免费"，而是**每一层你都知道它在干什么**：域名怎么解析、页面怎么构建、文件怎么传上去、证书怎么续、缓存怎么失效。出问题时你能定位到具体是哪一层，而不是对着一个"发布失败"的弹窗干瞪眼。

如果只是想写东西，平台确实更快。但如果你希望十年后这些文字还在、还能被一个 URL 直接打开——那值得花这两个晚上。

下一步我打算在这套地基上加两样东西：一个纯前端的工具页（不用后端就能跑），再往后才是用户系统。等做完了再写一篇。

# PDF 表格提取工具 - 外网部署指南

本说明提供三种方式，使外网用户通过网址访问本工具。

---

## 方式一：快速外网访问（内网穿透，适合演示/测试）

无需购买服务器，在本地运行服务后，用隧道把本机端口暴露到公网。

### 使用 Cloudflare Tunnel（推荐，免费）

1. 安装 [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)。
2. 在项目目录启动本地服务（仅开发/演示）：
   ```bash
   python start_server.py
   ```
   生产环境请使用标准命令：`gunicorn -w 4 --bind 0.0.0.0:$PORT --timeout 300 backend.wsgi:application`
3. 新开一个终端，运行：
   ```bash
   cloudflared tunnel --url http://localhost:5000
   ```
4. 终端会输出一行公网地址，形如：`https://xxxx-xx-xx-xx-xx.trycloudflare.com`，用浏览器打开即可。

### 使用 ngrok

1. 注册 [ngrok](https://ngrok.com)，安装并配置 token。
2. 启动本地服务后执行：
   ```bash
   ngrok http 5000
   ```
3. 使用界面里给出的 `Forwarding` 地址访问。

注意：内网穿透时，本机需保持开机且程序不关闭；免费隧道地址重启会变。

---

## 方式二：部署到 Render（免费云，一键部署）

[Render](https://render.com) 提供免费 Web 服务，适合长期挂一个可访问的网址。

### 步骤

1. 将本项目推送到 **GitHub**（或 GitLab）仓库。
2. 登录 [Render](https://dashboard.render.com)，点击 **New → Web Service**。
3. 连接你的仓库，选择该 PDF 表格提取项目。
4. 配置：
   - **Runtime**：选 **Docker**（使用项目里的 `Dockerfile`）。
   - **Instance Type**：选 **Free**。
   - 无需改 **Build Command** / **Start Command**（由 Dockerfile 和 Procfile 决定）。
5. 点击 **Create Web Service**，等待构建和启动。
6. 部署完成后，Render 会分配一个地址，如：`https://pdf-table-extract.onrender.com`，外网即可访问。

### 可选：不用 Docker，用 Python 原生

- **Build Command**：`pip install -r requirements.txt`
- **Start Command**：`gunicorn -w 4 --bind 0.0.0.0:$PORT --timeout 300 backend.wsgi:application`
- **Root Directory**：留空（仓库根目录）。

注意：免费实例约 15 分钟无访问会休眠，首次打开可能需等待几十秒；大文件上传可能受平台限制（通常约 100MB）。

---

## 方式三：自建服务器（Docker，适合正式使用）

在有公网 IP 的云服务器（阿里云、腾讯云、AWS 等）上用 Docker 部署，可长期稳定、自定义配置。

### 1. 服务器要求

- 系统：Linux（如 Ubuntu 22.04）
- 已安装 Docker：`curl -fsSL https://get.docker.com | sh`

### 2. 部署步骤

在**本机**构建镜像并导出（或使用 CI 构建后推送到镜像仓库），再在服务器上拉取并运行。这里以在服务器上直接构建为例（代码已通过 git 或拷贝到服务器）：

```bash
# 在项目根目录
docker build -t pdf-table-extract .
docker run -d --name pdf-app -p 8080:8080 pdf-table-extract
```

外网访问：`http://你的服务器IP:8080`。

### 3. 使用 Nginx 做反向代理（可选，支持 HTTPS）

若希望用 80/443 和域名访问，可在同一台机子上装 Nginx，例如：

```nginx
server {
    listen 80;
    server_name 你的域名.com;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 500M;
    }
}
```

再配置 SSL（如用 Let's Encrypt）即可实现 `https://你的域名.com`。

---

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `PORT` | 服务监听端口（云平台多会自动注入） | 5000 |
| `FLASK_DEBUG` | 是否开启调试（生产请关） | false |
| `UPLOAD_FOLDER` | 上传文件目录 | uploads |
| `OUTPUT_FOLDER` | 输出文件目录 | outputs |

---

## 部署后自检

- 打开首页应能看到「PDF表格提取工具」界面。
- 上传一个小 PDF，能识别表格并完成提取、下载，即说明前后端与 API 均正常。

若部署过程中某一步报错，可把报错信息或截图发给我，便于进一步排查。

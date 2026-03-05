# 使用 Render 部署 PDF 表格提取工具

按下面任选一种方式，即可把项目部署到 Render，获得一个外网可访问的网址。

---

## 方式 A：从 Render 控制台手动创建（推荐）

### 1. 把代码推到 GitHub

在项目目录执行（若尚未建仓）：

```bash
git init
git add .
git commit -m "Initial commit for Render deploy"
```

在 [GitHub](https://github.com/new) 新建一个仓库（如 `pdf-table-extract`），然后：

```bash
git remote add origin https://github.com/你的用户名/pdf-table-extract.git
git branch -M main
git push -u origin main
```

### 2. 在 Render 创建 Web Service

1. 打开 **[Render Dashboard](https://dashboard.render.com)**，登录/注册（可用 GitHub 登录）。
2. 点击 **New +** → **Web Service**。
3. **Connect a repository**：选 **GitHub**，授权后选择你刚推送的仓库（如 `pdf-table-extract`）。
4. 配置：
   - **Name**：可保持 `pdf-table-extract` 或自定。
   - **Region**：任选（如 Oregon）。
   - **Runtime**：选 **Docker**（项目已包含 `Dockerfile`）。
   - **Instance Type**：选 **Free**。
   - **Build Command**：留空（由 Dockerfile 负责构建）。
   - **Start Command**：留空（由 Dockerfile 的 `CMD` 启动）。
5. 点击 **Create Web Service**，等待首次构建和启动（约 3～5 分钟）。

### 3. 获取访问地址

- 部署成功后，在服务页顶部会显示 **Your service is live at** 下的地址，例如：  
  `https://pdf-table-extract.onrender.com`
- 用浏览器打开该地址即可使用 PDF 表格提取工具。

---

## 方式 B：用 Blueprint 一键部署（render.yaml）

若仓库根目录已有 `render.yaml`，可在 Render 用 Blueprint 一次性创建服务：

1. 确保代码已推送到 GitHub（同上）。
2. 打开 **[Render Dashboard](https://dashboard.render.com)** → **Blueprints**。
3. 点击 **New Blueprint Instance**，选择你的 GitHub 仓库。
4. Render 会读取根目录的 `render.yaml` 并创建其中的服务（如 `pdf-table-extract`）。
5. 创建完成后，在对应 Web Service 页面查看并访问给出的 URL。

---

## 部署后说明

- **免费实例**：约 15 分钟无访问会休眠，下次有人打开时再唤醒（可能需等待约 30 秒）。
- **大文件**：免费环境对请求体大小有限制（通常约 100MB），超大 PDF 若上传失败可考虑缩小文件或升级实例。
- **自定义域名**：在 Render 该 Web Service 的 **Settings → Custom Domains** 中可绑定自己的域名。

---

## 常见问题

**Q：构建失败，报错找不到 `backend.wsgi`？**  
A：确认仓库根目录下存在 `backend/wsgi.py` 和 `Dockerfile`，且 `Dockerfile` 里 `COPY backend ./backend` 已执行，然后重新部署。

**Q：访问网址一直转圈或 502？**  
A：多半是实例在休眠，多等几十秒再刷新；若仍不行，到 Render 该服务的 **Logs** 里查看是否有启动报错。

**Q：如何更新已部署的版本？**  
A：在本地改完代码后 `git push` 到同一分支，Render 会自动重新构建并部署（若已开启 Auto-Deploy）。

按上述任选一种方式操作即可完成 Render 部署；若某一步报错，把 Render 构建/运行日志里的报错贴出来，我可以帮你逐条排查。

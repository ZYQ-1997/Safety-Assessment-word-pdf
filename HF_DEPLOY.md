# 将项目部署到 Hugging Face Spaces

本项目已配置为在 Hugging Face Spaces 上以 **Docker** 方式运行，监听端口 **7860**（Spaces 默认）。无需绑卡，免费即可使用。

---

## 一、前置准备

1. **注册 Hugging Face 账号**  
   打开 [huggingface.co](https://huggingface.co/join) 注册并登录。

2. **安装 Git**（若尚未安装）  
   确保本机已安装 [Git](https://git-scm.com/)。

3. **（可选）安装 Hugging Face CLI**  
   便于登录与创建 Space，非必须。  
   ```bash
   pip install huggingface_hub
   ```

---

## 二、创建 Space 并推送代码

### 方式 A：在网页上创建 Space，再用 Git 推送（推荐）

1. **新建 Space**  
   - 打开 [huggingface.co/spaces](https://huggingface.co/spaces)  
   - 点击 **Create new Space**  
   - **Space name**：例如 `pdf-table-extract`  
   - **License**：选一个（如 MIT）  
   - **Space SDK**：选择 **Docker**  
   - **Space hardware**：免费选 **CPU basic** 即可  
   - 点击 **Create Space**

2. **在本地添加 HF 远程并推送**  
   在**本项目根目录**执行（把 `YOUR_USERNAME` 换成你的 HF 用户名）：

   ```bash
   # 若尚未初始化 git
   git init
   git add .
   git commit -m "Add Hugging Face Spaces support (Docker, port 7860)"

   # 添加 Hugging Face 远程（替换 YOUR_USERNAME 和 Space 名称）
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/pdf-table-extract

   # 若已存在 origin，可只加 hf 远程
   # git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/pdf-table-extract

   # 推送到 main（HF Spaces 默认拉取 main 分支）
   git push hf main
   ```

   若提示需要登录，在浏览器中完成登录，或使用 HF Token：

   ```bash
   git remote set-url hf https://YOUR_USERNAME:YOUR_HF_TOKEN@huggingface.co/spaces/YOUR_USERNAME/pdf-table-extract
   git push hf main
   ```

   Token 在：Hugging Face 网站 → **Settings → Access Tokens → New token**（需勾选 **write**）。

3. **等待构建**  
   推送后 Spaces 会自动根据仓库根目录的 **Dockerfile** 和 **README.md 中的 `app_port: 7860`** 构建并启动，在 Space 页面可看到构建日志。完成后即可在 Space 的 “App” 里访问应用。

---

### 方式 B：用 Hugging Face CLI 创建并上传

1. **登录**  
   ```bash
   huggingface-cli login
   ```
   按提示在浏览器中完成授权。

2. **创建 Space 并上传本目录**  
   ```bash
   cd "c:\Users\Z2200\Desktop\Safety Assessment"
   huggingface-cli repo create pdf-table-extract --type space --space_sdk docker
   git init
   git add .
   git commit -m "Add Hugging Face Spaces support"
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/pdf-table-extract
   git push -u hf main
   ```
   将 `YOUR_USERNAME` 替换为你的用户名。

---

## 三、重要文件说明

| 文件 | 作用 |
|------|------|
| **README.md 开头 YAML** | `sdk: docker`、`app_port: 7860`，供 Spaces 识别为 Docker 应用并转发到 7860 端口。 |
| **Dockerfile** | 构建镜像，容器内通过 `ENV PORT=7860` 使应用监听 7860。 |
| **backend/app.py** | 通过 `os.getenv("PORT", "5000")` 读端口；在 Docker 中由环境变量设为 7860。 |

本地直接运行 `python app.py` 时仍使用默认 5000；在 Spaces 的 Docker 中会使用 7860。

---

## 四、常见问题

- **构建失败**  
  查看 Space 页面的 **Logs**，确认 Dockerfile 和依赖无误；确保仓库根目录有 `Dockerfile`、`backend/`、`frontend/`、`requirements.txt`、`extract_all_tables.py`。

- **打开 Space 显示无法访问**  
  确认 README 顶部 YAML 中有 `app_port: 7860`，且 Dockerfile 中 `ENV PORT=7860` 与 `EXPOSE 7860` 已设置。

- **推送被拒绝**  
  检查是否用有 **write** 权限的 Token，或是否推送到正确的 `hf` 远程和 `main` 分支。

---

## 五、更新已部署的 Space

修改代码后，在项目根目录执行：

```bash
git add .
git commit -m "描述你的修改"
git push hf main
```

Spaces 会自动重新构建并发布新版本。

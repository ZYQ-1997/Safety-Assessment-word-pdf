# 部署环境变量说明（Vercel / Render / Streamlit 等）

在部署平台（如 Vercel、Render、Streamlit、Railway）的 **Environment Variables / 环境变量** 中可配置下表项。代码已通过 `backend/config.py` 安全读取，无需在业务代码里直接使用 `os.environ`。

---

## 环境变量一览表

| Key（变量名） | 作用 | 是否必填 | 默认值 | 示例/说明 |
|--------------|------|----------|--------|-----------|
| **PORT** | 服务监听端口。多数云平台会自动注入，无需手动设置。 | 否 | `5000` | 由 Render/Vercel 自动设置 |
| **FLASK_DEBUG** | 是否开启 Flask 调试模式。生产环境必须关闭，避免暴露堆栈等信息。 | 否 | `false` | 生产填 `false` 或留空；本地调试可设 `true` |
| **UPLOAD_FOLDER** | 上传文件保存目录（相对路径）。 | 否 | `uploads` | 仅相对路径，不要使用 `..` 或绝对路径 |
| **OUTPUT_FOLDER** | 提取结果输出目录（相对路径）。 | 否 | `outputs` | 同上 |
| **MAX_CONTENT_LENGTH_MB** | 允许的最大上传体积（单位：MB）。平台限制较小时可调小。 | 否 | `500` | 如 Vercel 限制 100MB 可设 `100` |

---

## 在部署平台如何配置

- **Vercel**：Project → Settings → Environment Variables，添加 Key / Value。
- **Render**：Web Service → Environment → Add Environment Variable。
- **Streamlit Cloud**：应用设置里的 “Secrets” 或 “Environment variables” 中配置。
- **Railway / 其他**：在服务或项目的 “Environment” / “Env” 中添加上述 Key 与 Value。

生产环境建议至少设置：

- `FLASK_DEBUG` = `false`（若平台不设则代码中默认即为 false）。

其余变量按需设置；不配置时使用上表中的默认值。

---

## 代码如何安全读取这些变量

所有部署相关配置都集中在 **`backend/config.py`** 中统一、安全地读取：

1. **类型与范围**
   - `PORT`：按整数解析，非法则回退默认 `5000`。
   - `FLASK_DEBUG`：仅将 `1/true/yes` 视为 True，其余为 False。
   - `MAX_CONTENT_LENGTH_MB`：限制在 1～500 之间，避免配置错误导致过大或过小。

2. **路径安全**
   - `UPLOAD_FOLDER` / `OUTPUT_FOLDER`：禁止包含 `..` 或绝对路径，否则回退为默认目录，避免路径穿越。

3. **使用方式**
   - 应用只从 `config` 模块导入常量使用，例如在 `backend/app.py` 中：
     - `from config import UPLOAD_FOLDER, OUTPUT_FOLDER, MAX_CONTENT_LENGTH, FLASK_DEBUG, PORT`
   - 不在业务逻辑里直接调用 `os.environ.get(...)`，便于统一修改默认值和校验规则。

如需新增环境变量，应在 **`backend/config.py`** 中增加读取与校验逻辑，再在本文档表格中补充 Key、作用与默认值。

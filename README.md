---
title: PDF表格提取工具
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# PDF表格提取工具

一个简单易用的PDF表格提取工具，可以从长文本PDF文件（支持600页以上）中完整提取所有表格，并导出为 PDF/表格 结果。

## 功能特点

- ✅ 支持大文件PDF（最大500MB）
- ✅ 自动提取PDF中的所有表格
- ✅ 导出为Excel格式，每个表格单独一个工作表
- ✅ 简洁美观的前端界面
- ✅ 支持拖拽上传
- ✅ 实时显示处理进度

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务

**本地开发：**
```bash
python start_server.py
# 或：cd backend && python app.py
```

**生产环境（标准命令，部署时使用 Procfile / Dockerfile 或以下命令）：**
```bash
# 从项目根目录执行；PORT 由环境变量指定
gunicorn -w 4 --bind 0.0.0.0:$PORT --timeout 300 backend.wsgi:application
```
若平台未自动设置工作目录，可先设置：`export PYTHONPATH=.` 或 `set PYTHONPATH=.`（Windows）。

### 3. 打开前端界面

在浏览器中打开 `frontend/index.html` 文件，或者使用本地服务器：

```bash
# 使用Python启动简单HTTP服务器
cd frontend
python -m http.server 8000
```

然后在浏览器中访问 `http://localhost:8000`

## 使用方法

1. **上传PDF文件**
   - 点击上传区域选择文件，或直接拖拽PDF文件到上传区域
   - 支持最大500MB的PDF文件

2. **提取表格**
   - 文件上传成功后，点击"提取表格"按钮
   - 系统会自动处理PDF文件并提取所有表格
   - 处理过程中会显示进度条

3. **下载结果**
   - 提取完成后，会显示提取的表格数量
   - 点击"下载结果"按钮下载Excel文件
   - Excel文件中每个表格都在单独的工作表中

## 项目结构

```
Safety Assessment/
├── backend/
│   ├── app.py              # Flask后端应用
│   ├── uploads/            # 上传文件临时存储目录
│   └── outputs/            # 提取结果输出目录
├── frontend/
│   └── index.html          # 前端界面
├── requirements.txt        # Python依赖包
└── README.md              # 项目说明文档
```

## API接口说明

### 1. 文件上传
- **URL**: `/api/upload`
- **方法**: `POST`
- **参数**: `file` (multipart/form-data)
- **返回**: JSON格式，包含文件名等信息

### 2. 提取表格
- **URL**: `/api/extract`
- **方法**: `POST`
- **参数**: JSON格式，包含 `filename`
- **返回**: JSON格式，包含表格数量和下载链接

### 3. 下载结果
- **URL**: `/api/download/<filename>`
- **方法**: `GET`
- **返回**: Excel文件

### 4. 健康检查
- **URL**: `/api/health`
- **方法**: `GET`
- **返回**: 服务状态

## 技术栈

- **后端**: Flask, pdfplumber, pandas, openpyxl
- **前端**: HTML, CSS, JavaScript (原生)
- **文件处理**: pdfplumber (PDF解析), pandas (数据处理), openpyxl (Excel生成)

## 注意事项

1. 处理大文件（600页以上）时，可能需要较长时间，请耐心等待
2. 确保有足够的磁盘空间存储上传的文件和输出结果
3. 提取的表格会按页面和表格索引命名工作表
4. 如果PDF中没有表格，会返回相应提示信息

## 常见问题

### 关于开发服务器警告
启动后端服务时，您可能会看到以下警告：
```
WARNING: This is a development server. Do not use it in a production deployment.
```
这是**正常的提示信息**，表示当前使用的是Flask开发服务器。对于本地开发和测试完全没问题，可以安全忽略此警告。

### 后端服务无法启动
- 检查Python版本（建议3.8+）
- 确认所有依赖包已正确安装
- 检查5000端口是否被占用

### 前端无法连接后端
- 确认后端服务已启动
- 检查 `frontend/index.html` 中的 `API_BASE_URL` 是否正确
- 如果使用不同的端口，需要修改前端代码中的API地址

### 文件上传失败
- 检查文件大小是否超过500MB限制
- 确认文件格式为PDF
- 检查 `backend/uploads` 目录是否有写入权限

## 许可证

本项目仅供学习和研究使用。

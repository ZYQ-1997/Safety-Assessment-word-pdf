@echo off
chcp 65001 >nul
echo ====================================
echo PDF表格提取工具 - 启动脚本
echo ====================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo 正在检查依赖包...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

echo.
echo 正在启动后端服务...
echo 后端服务地址: http://localhost:5000
echo.
echo 请在浏览器中打开 frontend/index.html 使用前端界面
echo 或访问 http://localhost:5000 查看API状态
echo.
echo 按 Ctrl+C 停止服务
echo.

cd backend
python app.py

pause

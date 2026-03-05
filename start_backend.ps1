# 启动后端服务器脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "正在启动PDF表格提取后端服务..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切换到项目目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "错误: 未找到Python，请先安装Python" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

# 切换到backend目录并启动服务器
Set-Location "backend"
Write-Host ""
Write-Host "前端界面: http://localhost:5000" -ForegroundColor Yellow
Write-Host "API接口: http://localhost:5000/api" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动Flask服务器
python app.py


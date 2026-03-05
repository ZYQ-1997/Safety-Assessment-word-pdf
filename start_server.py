"""
【仅限本地开发】启动后端服务器（Flask 开发服务器，debug=True）。
生产部署请使用标准命令：gunicorn backend.wsgi:application（见 Procfile / Dockerfile）
适用于 GitHub Codespaces：监听 0.0.0.0:5000 以便端口转发。
"""
import os
import sys

# 获取项目根目录（本脚本所在目录）
project_root = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(project_root, 'backend')
app_py = os.path.join(backend_dir, 'app.py')

# 明确检查 backend/app.py 是否存在
if not os.path.isfile(app_py):
    print("错误: 未找到 backend/app.py")
    print(f"  期望路径: {app_py}")
    print(f"  当前项目根: {project_root}")
    print("请确认：1) 在项目根目录执行本脚本  2) backend 文件夹与 app.py 已存在（如未提交请 git add backend/）")
    sys.exit(1)

# 切换到 backend 目录
os.chdir(backend_dir)
# 确保 backend 在 Python 路径中
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Codespaces/云环境：优先使用 PORT 环境变量，默认 5000
_port = os.environ.get("PORT", "5000")
port = int(_port) if str(_port).strip().isdigit() else 5000

try:
    from app import app
    print("=" * 60)
    print("PDF表格提取服务启动中...")
    print("=" * 60)
    print(f"前端界面: http://0.0.0.0:{port}")
    print(f"API接口: http://0.0.0.0:{port}/api")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务\n")
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
except KeyboardInterrupt:
    print("\n\n服务器已停止")
except Exception as e:
    print(f"\n启动失败: {e}")
    import traceback
    traceback.print_exc()
    try:
        input("\n按Enter键退出...")
    except EOFError:
        pass
    sys.exit(1)


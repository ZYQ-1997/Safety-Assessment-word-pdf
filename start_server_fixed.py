"""
【仅限本地开发】启动后端服务器（修复版，Flask 开发服务器）。
生产部署请使用：python start_production.py 或 gunicorn backend.wsgi:application
"""
import os
import sys

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(project_root, 'backend')
frontend_dir = os.path.join(project_root, 'frontend')

print(f"项目根目录: {project_root}")
print(f"Backend目录: {backend_dir}")
print(f"Frontend目录: {frontend_dir}")
print(f"Frontend目录存在: {os.path.exists(frontend_dir)}")
print(f"index.html存在: {os.path.exists(os.path.join(frontend_dir, 'index.html'))}")

# 切换到backend目录
os.chdir(backend_dir)
print(f"\n切换到backend目录: {os.getcwd()}")

# 确保backend目录在Python路径中
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 导入并运行app
try:
    print("\n正在导入app模块...")
    from app import app
    
    # 验证前端路径
    print(f"\nFlask静态文件夹: {app.static_folder}")
    print(f"静态文件夹存在: {os.path.exists(app.static_folder) if app.static_folder else False}")
    
    print("\n" + "=" * 60)
    print("PDF表格提取服务启动中...")
    print("=" * 60)
    print("前端界面: http://localhost:5000")
    print("API接口: http://localhost:5000/api")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务\n")
    
    # 启动服务器
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    
except KeyboardInterrupt:
    print("\n\n服务器已停止")
except Exception as e:
    print(f"\n启动失败: {e}")
    import traceback
    traceback.print_exc()
    input("\n按Enter键退出...")
    sys.exit(1)





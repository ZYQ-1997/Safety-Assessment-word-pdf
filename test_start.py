"""测试启动服务器"""
import os
import sys

# 获取backend目录路径
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
print(f"Backend目录: {backend_dir}")
print(f"目录存在: {os.path.exists(backend_dir)}")

# 切换到backend目录
os.chdir(backend_dir)
print(f"当前工作目录: {os.getcwd()}")

# 确保backend目录在Python路径中
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
print(f"Python路径已更新")

# 导入并运行app
try:
    print("正在导入app模块...")
    from app import app
    print("✓ app模块导入成功")
    print(f"✓ Flask应用创建成功")
    print(f"✓ 路由数量: {len(list(app.url_map.iter_rules()))}")
    print("\n" + "=" * 50)
    print("PDF表格提取服务启动中...")
    print("=" * 50)
    print("前端界面: http://localhost:5000")
    print("API接口: http://localhost:5000/api")
    print("=" * 50)
    print("\n按 Ctrl+C 停止服务\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
except KeyboardInterrupt:
    print("\n\n服务器已停止")
except Exception as e:
    print(f"\n启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)





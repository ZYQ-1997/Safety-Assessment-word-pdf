"""
生产环境启动脚本
使用 Gunicorn 或 Waitress 作为 WSGI 服务器
"""
from app import app

if __name__ == '__main__':
    # 生产环境配置
    app.run(debug=False, host='0.0.0.0', port=5000)

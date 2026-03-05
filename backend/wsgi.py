# -*- coding: utf-8 -*-
"""生产环境 WSGI 入口，供 gunicorn 等使用"""
import os
import sys

# 确保 backend 在路径中（部署时工作目录可能为项目根）
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app as application

if __name__ == '__main__':
    _port = os.getenv("PORT", "5000")
    port = int(_port) if str(_port).strip().isdigit() else 5000
    application.run(host='0.0.0.0', port=port)

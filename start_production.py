# -*- coding: utf-8 -*-
"""
已废弃：生产环境请使用标准命令，不要依赖本脚本。

标准启动方式：
  - 从项目根目录执行：gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 300 backend.wsgi:application
  - 或使用 Procfile / Dockerfile（部署平台会自动使用）

若需在本地模拟生产，可在项目根目录执行：
  PYTHONPATH=. gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 300 backend.wsgi:application
"""
import os
import sys
import subprocess

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    port = os.environ.get("PORT", "5000")
    env = os.environ.copy()
    env["PYTHONPATH"] = root
    print("Deprecated: use 'gunicorn backend.wsgi:application' from project root. Running it for you...")
    subprocess.run(
        [sys.executable, "-m", "gunicorn", "--bind", f"0.0.0.0:{port}", "--workers", "1", "--threads", "4", "--timeout", "300", "backend.wsgi:application"],
        cwd=root,
        env=env,
        check=True,
    )

if __name__ == "__main__":
    main()

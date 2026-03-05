# PDF表格提取工具 - 生产镜像
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend
COPY extract_all_tables.py .

ENV PYTHONPATH=/app
ENV PORT=8080
EXPOSE 8080

# 入口说明：Flask 实例在 backend/app.py 变量名为 app；backend/wsgi.py 将其导出为 application，故使用 backend.wsgi:application
CMD ["gunicorn", "-w", "4", "backend.wsgi:application", "--bind", "0.0.0.0:8080", "--timeout", "300"]

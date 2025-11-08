# ============================================
# POSX Backend - Development Dockerfile
# ============================================

FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制 requirements
COPY requirements/ /app/requirements/

# 安装 Python 依赖（开发版本）
RUN pip install --no-cache-dir -r requirements/local.txt

# 复制应用代码
COPY . /app/

# 暴露端口
EXPOSE 8000

# 默认命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# 构建阶段
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# 最小化安装依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
# 升级 pip 并全局安装依赖
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# # 调试：验证依赖是否正确安装
# RUN ls -la /usr/local

# 运行阶段
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    DEBUG=false

WORKDIR /app

# 复制全局依赖
COPY --from=builder /usr/local /usr/local

COPY more_core.py .
RUN chmod +x more_core.py
COPY degpt.py .
RUN chmod +x degpt.py

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

EXPOSE ${PORT}

CMD ["python", "more_core.py"]

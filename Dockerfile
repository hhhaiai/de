# Build stage
FROM python:3.11-slim-bullseye AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /build

# 优化系统依赖安装
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 优化Python包安装和Playwright安装
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium --with-deps && \
    rm -rf /root/.cache/pip && \
    rm -rf /root/.cache/ms-playwright/node* && \
    find /root/.cache/ms-playwright -name "*.zip" -delete

# Runtime stage
FROM python:3.11-slim-bullseye AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    DEBUG=false \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# 优化运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 优化文件复制
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /root/.cache/ms-playwright/chromium-* /ms-playwright/

# 创建非root用户
RUN useradd -ms /bin/bash appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /ms-playwright

# 只复制必要文件
COPY --chown=appuser:appuser more_core.py degpt.py requirements.txt ./

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

CMD ["python", "more_core.py"]
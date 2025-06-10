FROM python:3.12-slim-bookworm

# Install uv (from official binary), nodejs, npm, and git
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    # 安裝 ffmpeg 和 ffprobe (open-webui 可能需要處理音檔)
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm via NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Confirm npm and node versions (optional debugging info)
RUN node -v && npm -v

# Copy your mcpo source code (assuming in src/mcpo) and the start script
COPY . /app
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

WORKDIR /app

# Create virtual environment explicitly in known location
ENV VIRTUAL_ENV=/app/.venv
RUN uv venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install mcpo (assuming pyproject.toml is properly configured)
# 注意：mcpo 如果需要 mcp 套件，確保 pyproject.toml 有包含，或單獨安裝 mcp
RUN uv pip install . && rm -rf ~/.cache

# Install open-webui
RUN uv pip install open-webui && rm -rf ~/.cache

RUN uv pip install exa-py

# Verify mcpo installed correctly (optional)
RUN which mcpo || echo "mcpo not found"

# 建立 config 目錄 (複製 config.json 在 run 時掛載會覆蓋這裡的複製)
# COPY config/config.json /app/config/config.json # 移除這行，改為只建立目錄

RUN mkdir -p /app/config

# 定義 volume 供外部掛載 (提供 config.json)
VOLUME ["/app/config"]

# Expose ports for mcpo (8000) and open-webui (8080)
EXPOSE 8000 8080

# 設定容器啟動時執行的命令為 start.sh
ENTRYPOINT ["/app/start.sh"]

# CMD 用於在 ENTRYPOINT 後傳遞額外參數，這裡不需要
CMD []
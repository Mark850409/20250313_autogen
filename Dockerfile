# 使用適當的基礎映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 AutogenStudio 相關依賴
RUN pip install --upgrade pip setuptools wheel
RUN pip install autogenstudio

# 創建並掛載目錄
VOLUME [ "/data" ]

# 設定環境變數
ENV DATA_DIR=/data

# 容器啟動時進入 AutogenStudio
CMD ["autogenstudio", "--data-dir", "/data"]

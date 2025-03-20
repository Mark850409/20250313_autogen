# 使用 Python 3.12 slim 版本作為基底映像
FROM python:3.12-slim

# 設定容器內的工作目錄
WORKDIR /app

# 創建新的使用者 autogen 並設定權限
RUN groupadd -r autogen && \
    useradd -r -g autogen -d /app -s /bin/bash autogen

# 變更 /app 目錄擁有者為 autogen
RUN chown autogen:autogen /app

# 設定 autogen 使用者的主目錄
ENV HOME=/app

# 切換至 autogen 使用者
USER autogen

# 複製並安裝 Python 依賴
COPY --chown=autogen:autogen requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 創建並掛載 /data 目錄
VOLUME [ "/data" ]

# 暴露 AutogenStudio 服務的端口
EXPOSE 8081

# 設定容器啟動時執行的指令
ENTRYPOINT ["/app/.local/bin/autogenstudio", "ui", "--host", "0.0.0.0", "--port", "8081"]

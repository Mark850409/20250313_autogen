FROM mcr.microsoft.com/devcontainers/python:3.10

WORKDIR /code

# 安裝必要的套件
RUN pip install -U gunicorn autogenstudio fastapi uvicorn pydantic

# 複製 requirements.txt 並安裝依賴
COPY requirements.txt /code/
RUN pip install -r requirements.txt

# 為 autogen_api.py 安裝額外的依賴
RUN pip install autogen

RUN useradd -m -u 100000 user
USER user
ENV HOME=/home/user 
ENV PATH=/home/user/.local/bin:$PATH 
ENV AUTOGENSTUDIO_APPDIR=/home/user/app
ENV PORT=8080
ENV API_PORT=8500

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

# 創建啟動腳本
RUN echo '#!/bin/bash\n\
# 啟動 autogen_api 在背景執行\n\
gunicorn -w 2 --timeout 12600 -k uvicorn.workers.UvicornWorker autogen_api:app --bind "0.0.0.0:$API_PORT" &\n\
\n\
# 啟動 AutoGen Studio\n\
gunicorn -w $((2 * $(getconf _NPROCESSORS_ONLN) + 1)) --timeout 12600 -k uvicorn.workers.UvicornWorker autogenstudio.web.app:app --bind "0.0.0.0:$PORT"\n\
' > $HOME/app/start.sh && chmod +x $HOME/app/start.sh

# 使用啟動腳本
CMD ["./start.sh"]

EXPOSE $PORT $API_PORT
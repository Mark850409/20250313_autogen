FROM mcr.microsoft.com/devcontainers/python:3.10

WORKDIR /code

# 安裝必要的套件
RUN pip install -U gunicorn autogenstudio fastapi uvicorn pydantic

# 為 autogen_api.py 安裝額外的依賴
RUN pip install autogen autogen-ext autogen-agentchat autogen-core pyautogen mcp exa-py

RUN useradd -m -u 100000 user
USER user
ENV HOME=/home/user 
ENV PATH=/home/user/.local/bin:$PATH 
ENV AUTOGENSTUDIO_APPDIR=/home/user/app
ENV PORT=8080

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

CMD gunicorn -w $((2 * $(getconf _NPROCESSORS_ONLN) + 1)) --timeout 12600 -k uvicorn.workers.UvicornWorker autogenstudio.web.app:app --bind "0.0.0.0:$PORT"

EXPOSE $PORT
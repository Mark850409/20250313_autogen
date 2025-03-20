FROM python:3.10-slim

WORKDIR /code

RUN pip install -U gunicorn autogenstudio fastapi uvicorn pydantic

RUN pip install autogen autogen-ext autogen-agentchat autogen-core pyautogen mcp exa-py
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user 
ENV PATH=/home/user/.local/bin:$PATH 
ENV AUTOGENSTUDIO_APPDIR=/home/user/app
ENV PORT=8081
WORKDIR $HOME/app

COPY --chown=user . $HOME/app

CMD gunicorn -w $((2 * $(getconf _NPROCESSORS_ONLN) + 1)) --timeout 12600 -k uvicorn.workers.UvicornWorker autogenstudio.web.app:app --bind "0.0.0.0:8081"

# 暴露 AutogenStudio 服務的端口
EXPOSE 8081
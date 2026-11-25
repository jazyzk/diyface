FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DIYFACE_ASSETS=/app/assets \
    PORT=8000

WORKDIR /app

# 先装依赖，代码改动时不必重装
COPY pyproject.toml README.md ./
COPY src ./src
COPY assets ./assets

RUN pip install --no-cache-dir .

EXPOSE 8000

# 云平台会注入 PORT（Render 默认 10000），本地不注入时退回 8000
CMD ["sh", "-c", "exec waitress-serve --listen=0.0.0.0:${PORT:-8000} diyface.app:app"]

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 先装依赖，代码改动时不必重装
COPY pyproject.toml README.md ./
COPY src ./src
COPY assets ./assets

RUN pip install --no-cache-dir .

EXPOSE 8000

# waitress 是跨平台的 WSGI 服务器，Windows / Linux 都能跑
CMD ["python", "-m", "waitress", "--host=0.0.0.0", "--port=8000", "diyface.app:app"]

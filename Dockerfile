FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.14.7 AS local

COPY --from=uv /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Graphviz 시스템 의존성 추가
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    libgraphviz-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# 실제 소스 코드는 compose의 volume으로 마운트합니다.
VOLUME ["/workspace/src"]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]

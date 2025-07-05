FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY uv.lock pyproject.toml /app/
RUN uv sync
COPY . .
CMD ["uv", "run", "app.py"]
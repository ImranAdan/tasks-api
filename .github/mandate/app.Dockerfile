# Builds a pull request's app so it can run sealed off. Built from main's copy of
# this file, with the pull request's code as the build context.
FROM python:3.12-slim@sha256:e695ab189fa2d082b1c61c69a6b888a5adeca61ceeccad107b1ed2a125721a9e
RUN pip install --no-cache-dir uv==0.9.14
WORKDIR /app
COPY . .
RUN uv sync --locked --no-dev
USER 65534
CMD [".venv/bin/uvicorn", "tasks_api:app", "--host", "0.0.0.0", "--port", "8000"]

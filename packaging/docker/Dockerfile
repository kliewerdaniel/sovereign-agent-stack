FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir ".[dashboard]"

EXPOSE 8080

ENTRYPOINT ["python", "-m", "sas.dashboard.server"]
CMD ["--host", "0.0.0.0", "--port", "8080"]

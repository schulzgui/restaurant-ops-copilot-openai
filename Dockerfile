FROM python:3.12-slim
WORKDIR /app
COPY src ./src
COPY data ./data
ENV PYTHONPATH=/app/src PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home copilot && mkdir runtime && chown copilot:copilot runtime
USER copilot
EXPOSE 8004
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8004/health', timeout=2)"
CMD ["python", "-m", "ops_copilot.cli", "serve", "--host", "0.0.0.0"]


FROM python:3.9-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080"]

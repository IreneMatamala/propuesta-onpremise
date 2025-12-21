# Multi-stage build para optimizar tamaño
# Stage 1: Builder
FROM python:3.9-slim as builder

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.9-slim

# Crear usuario no root
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && chown -R appuser:appuser /app

WORKDIR /app

# Copiar entorno virtual del stage 1
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

USER appuser

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_APP=wsgi.py

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health', timeout=2)"

# Exponer puerto
EXPOSE 8000

# Comando de ejecución
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "wsgi:app"]

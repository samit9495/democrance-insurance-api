# Multi-stage build: a wheels stage keeps build tooling out of the final image,
# which runs as a non-root user and serves via gunicorn.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements/ requirements/
RUN pip install --upgrade pip && pip wheel --wheel-dir /wheels -r requirements/base.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    PORT=8000

# libpq is needed at runtime by psycopg; curl powers the container healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements/ requirements/
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements/base.txt \
    && rm -rf /wheels

COPY . .

# Collect static at build time so the image is immutable and start-up is fast.
# A throwaway key/host lets collectstatic import prod settings without secrets.
RUN SECRET_KEY=build-only ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

RUN chmod +x /app/scripts/docker-entrypoint.sh && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/healthz/" || exit 1

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]

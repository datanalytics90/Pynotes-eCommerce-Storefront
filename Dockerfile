FROM node:20-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY tailwind.config.js postcss.config.js ./
COPY static_src/ ./static_src/
COPY templates/ ./templates/
COPY apps/ ./apps/
RUN npx tailwindcss -i ./static_src/input.css -o ./static/css/output.css --minify

FROM python:3.11-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /app/static/css/output.css ./static/css/output.css

# Build-time-only placeholders so collectstatic can import settings without real secrets.
# Real values are supplied at runtime via docker-compose / the hosting platform's env vars.
RUN SECRET_KEY=build-placeholder ALLOWED_HOSTS=localhost DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

RUN useradd --system --uid 10001 --no-create-home app
RUN chown -R app:app /app
USER app
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py create_admin && gunicorn config.wsgi:application --bind 0.0.0.0:8080"]

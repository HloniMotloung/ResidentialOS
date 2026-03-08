FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000
```

---

## 11. `requirements/base.txt`
```
django>=5.0,<6.0
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
psycopg2-binary>=2.9
celery>=5.3
redis>=5.0
django-celery-beat>=2.6
django-filter>=23.0
pillow>=10.0
boto3>=1.34          # S3 file storage
django-storages>=1.14
sendgrid>=6.11
twilio>=8.0
python-decouple>=3.8 # .env management
gunicorn>=21.0
sentry-sdk>=1.40
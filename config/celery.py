import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("residentialos")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "generate-monthly-levies": {
        "task":     "apps.levies.tasks.generate_monthly_levies",
        "schedule": crontab(hour=0, minute=5, day_of_month=1),
    },
    "send-overdue-reminders": {
        "task":     "apps.levies.tasks.send_overdue_reminders",
        "schedule": crontab(hour=8, minute=0, day_of_month=7),
    },
}
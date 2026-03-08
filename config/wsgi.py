import os
from django.core.wsgi import get_wsgi_application

# Render sets DJANGO_SETTINGS_MODULE in the environment.
# Locally it defaults to local settings.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = get_wsgi_application()

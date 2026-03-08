from django.core.management.base import BaseCommand
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Creates a superuser non-interactively'

    def handle(self, *args, **kwargs):
        username = 'admin'
        email    = 'maclucia340@gmail.com'
        password = 'Dk34209Ano'

        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Superuser "{username}" already exists — skipping.')
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(f'Superuser "{username}" created successfully.')
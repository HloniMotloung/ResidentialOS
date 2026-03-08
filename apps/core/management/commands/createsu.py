from django.core.management.base import BaseCommand
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Creates a superuser non-interactively'

    def handle(self, *args, **kwargs):
        username = 'admin'
        email    = 'cata@email.com'
        password = 'M@nager@2026'

        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Superuser "{username}" already exists — skipping.')
        else:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            user.status    = 'approved'
            user.is_active = True
            user.save()
            self.stdout.write(f'Superuser "{username}" created successfully.')

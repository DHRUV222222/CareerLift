from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Creates a superuser if none exists, or updates the password if it does'

    def handle(self, *args, **options):
        User = get_user_model()
        admin_username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        admin_password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        
        if not admin_password or admin_password == 'admin123':
            self.stdout.write(
                self.style.WARNING('Using default admin password. Please set DJANGO_SUPERUSER_PASSWORD in production.')
            )

        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {admin_username}')
            )
        else:
            user = User.objects.get(username=admin_username)
            user.set_password(admin_password)
            user.email = admin_email
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated password for existing superuser: {admin_username}')
            )

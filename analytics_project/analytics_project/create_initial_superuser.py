# realty_analytics/management/commands/create_initial_superuser.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = 'Создает суперпользователя, если он еще не существует.'

    def handle(self, *args, **kwargs):
        # Используем переменные окружения для безопасности,
        # но для MVP можно временно задать их прямо здесь.
        # ВАЖНО: Не храните реальные пароли в коде в продакшене!
        # Для MVP это допустимо.
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'YourSecurePassword123') # ЗАМЕНИТЕ НА СВОЙ ПАРОЛЬ

        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"Создание суперпользователя: {username}")
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Суперпользователь {username} успешно создан."))
        else:
            self.stdout.write(self.style.WARNING(f"Суперпользователь {username} уже существует."))
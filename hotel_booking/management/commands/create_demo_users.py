from django.core.management.base import BaseCommand
from hotel_booking.models import User


class Command(BaseCommand):
    help = 'Создает демо-пользователей для тестирования'

    def handle(self, *args, **options):
        # Создание обычного пользователя
        if not User.objects.filter(username='user').exists():
            user = User.objects.create_user(
                username='user',
                email='user@example.com',
                password='user12345',
                first_name='Иван',
                last_name='Петров',
                phone='+7 (999) 123-45-67',
                role='user'
            )
            self.stdout.write(self.style.SUCCESS(f'Создан пользователь: {user.username}'))

        # Создание менеджера
        if not User.objects.filter(username='manager').exists():
            manager = User.objects.create_user(
                username='manager',
                email='manager@example.com',
                password='manager12345',
                first_name='Анна',
                last_name='Сидорова',
                phone='+7 (999) 234-56-78',
                role='manager'
            )
            self.stdout.write(self.style.SUCCESS(f'Создан менеджер: {manager.username}'))

        # Создание администратора
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin12345',
                first_name='Admin',
                last_name='Adminov',
                phone='+7 (999) 345-67-89',
                role='admin'
            )
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Создан администратор: {admin.username}'))

        self.stdout.write(self.style.SUCCESS('Демо-пользователи успешно созданы!'))
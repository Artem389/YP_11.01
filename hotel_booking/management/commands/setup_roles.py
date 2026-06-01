from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hotel_booking.models import Guest


class Command(BaseCommand):
    help = 'Создает пользователей с разными ролями'

    def handle(self, *args, **options):
        # Создание администратора
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            Guest.objects.create(
                user=admin_user,
                phone='+7 (999) 000-00-00',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS('Администратор создан: admin / admin123'))

        # Создание менеджера
        if not User.objects.filter(username='manager').exists():
            manager_user = User.objects.create_user(
                username='manager',
                email='manager@example.com',
                password='manager123',
                first_name='Manager',
                last_name='User'
            )
            Guest.objects.create(
                user=manager_user,
                phone='+7 (999) 111-11-11',
                role='manager'
            )
            self.stdout.write(self.style.SUCCESS('Менеджер создан: manager / manager123'))

        # Создание обычного гостя
        if not User.objects.filter(username='guest').exists():
            guest_user = User.objects.create_user(
                username='guest',
                email='guest@example.com',
                password='guest123',
                first_name='Guest',
                last_name='User'
            )
            Guest.objects.create(
                user=guest_user,
                phone='+7 (999) 222-22-22',
                role='guest'
            )
            self.stdout.write(self.style.SUCCESS('Гость создан: guest / guest123'))

        self.stdout.write(self.style.SUCCESS('Все роли созданы!'))
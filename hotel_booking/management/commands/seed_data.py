from django.core.management.base import BaseCommand
from hotel_booking.models import User, Hotel, Room, Service
from decimal import Decimal


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def handle(self, *args, **options):
        # Создание отелей
        hotels = [
            {'name': 'Grand Hotel Moscow', 'city': 'Москва', 'stars': 5, 'address': 'ул. Тверская, 10',
             'phone': '+7 (495) 123-45-67', 'email': 'info@grandhotel.ru'},
            {'name': 'St. Petersburg Palace', 'city': 'Санкт-Петербург', 'stars': 5, 'address': 'Невский пр., 100',
             'phone': '+7 (812) 234-56-78', 'email': 'info@palace.ru'},
            {'name': 'Sochi Beach Resort', 'city': 'Сочи', 'stars': 4, 'address': 'ул. Приморская, 5',
             'phone': '+7 (862) 345-67-89', 'email': 'info@sochibeach.ru'},
        ]

        for hotel_data in hotels:
            hotel, created = Hotel.objects.get_or_create(
                name=hotel_data['name'],
                defaults=hotel_data
            )
            self.stdout.write(f'{"Создан" if created else "Существует"} отель: {hotel.name}')

            # Создание номеров для отеля
            room_types = ['single', 'double', 'suite']
            prices = [5000, 8000, 15000]

            for i, (room_type, price) in enumerate(zip(room_types, prices), 1):
                Room.objects.get_or_create(
                    hotel=hotel,
                    room_number=f"{hotel.id}{i}01",
                    defaults={
                        'room_type': room_type,
                        'price_per_night': Decimal(price),
                        'capacity': 2 if room_type == 'double' else 1,
                        'is_available': True
                    }
                )
            self.stdout.write(f'  Созданы номера для отеля {hotel.name}')

        # Создание услуг
        services = [
            {'name': 'Завтрак', 'description': 'Шведский стол', 'price': 1500},
            {'name': 'Спа-центр', 'description': 'Посещение спа-центра', 'price': 3000},
            {'name': 'Трансфер', 'description': 'Трансфер из аэропорта', 'price': 2500},
            {'name': 'Парковка', 'description': 'Охраняемая парковка', 'price': 1000},
        ]

        for service_data in services:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            self.stdout.write(f'{"Создана" if created else "Существует"} услуга: {service.name}')

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена тестовыми данными!'))
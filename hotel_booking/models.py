from django.db import models
from django.contrib.auth.models import User

class Hotel(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название отеля")
    address = models.TextField(verbose_name="Адрес")
    description = models.TextField(blank=True, verbose_name="Описание")
    stars = models.IntegerField(default=3, verbose_name="Количество звёзд")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Отель"
        verbose_name_plural = "Отели"

class Room(models.Model):
    ROOM_TYPES = [
        ('standart', 'Стандарт'),
        ('junior', 'Полулюкс'),
        ('lux', 'Люкс'),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms', verbose_name="Отель")
    room_number = models.CharField(max_length=10, verbose_name="Номер комнаты")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='standart', verbose_name="Тип номера")
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена за ночь")
    capacity = models.IntegerField(default=2, verbose_name="Вместимость (чел)")
    is_available = models.BooleanField(default=True, verbose_name="Доступен")

    def __str__(self):
        return f"{self.hotel.name} - {self.room_number}"

    class Meta:
        verbose_name = "Номер"
        verbose_name_plural = "Номера"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="Номер")
    check_in_date = models.DateField(verbose_name="Дата заезда")
    check_out_date = models.DateField(verbose_name="Дата выезда")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата бронирования")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    def __str__(self):
        return f"Бронь {self.user.username} - {self.room}"

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
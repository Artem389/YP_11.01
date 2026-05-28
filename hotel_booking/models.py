from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Hotel(models.Model):
    """Модель отеля"""
    name = models.CharField(max_length=200, verbose_name="Название отеля")
    address = models.TextField(verbose_name="Адрес")
    description = models.TextField(blank=True, verbose_name="Описание")
    stars = models.IntegerField(default=3, verbose_name="Количество звезд", choices=[(i, f"{i} звезд") for i in range(1, 6)])
    phone = models.CharField(max_length=20, verbose_name="Телефон", null=True, blank=True)
    email = models.EmailField(verbose_name="Email", null=True, blank=True)
    check_in_time = models.TimeField(default='14:00', verbose_name="Время заезда")
    check_out_time = models.TimeField(default='12:00', verbose_name="Время выезда")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.name

    def can_delete(self):
        """Проверка, можно ли удалить отель"""
        return not self.rooms.exists()  # Нет номеров

    def get_delete_warning(self):
        """Получить предупреждение при удалении"""
        if self.rooms.exists():
            rooms_count = self.rooms.count()
            bookings_count = Booking.objects.filter(room__hotel=self).count()
            return f"В отеле есть {rooms_count} номер(ов) и {bookings_count} бронирование(й). Удаление невозможно, пока есть номера."
        return None

    class Meta:
        verbose_name = "Отель"
        verbose_name_plural = "Отели"
        ordering = ['-stars', 'name']


class Room(models.Model):
    """Модель номера"""
    ROOM_TYPES = [
        ('standart', 'Стандарт'),
        ('junior', 'Полулюкс'),
        ('lux', 'Люкс'),
        ('president', 'Президентский'),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms', verbose_name="Отель")  # Изменено с PROTECT на CASCADE
    room_number = models.CharField(max_length=10, verbose_name="Номер комнаты")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='standart', verbose_name="Тип номера")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за ночь")
    capacity = models.IntegerField(default=2, verbose_name="Вместимость (чел)")
    square = models.DecimalField(max_digits=5, decimal_places=1, verbose_name="Площадь (кв.м)", null=True, blank=True)
    has_wifi = models.BooleanField(default=True, verbose_name="Wi-Fi")
    has_tv = models.BooleanField(default=True, verbose_name="Телевизор")
    has_air_conditioning = models.BooleanField(default=True, verbose_name="Кондиционер")
    description = models.TextField(blank=True, verbose_name="Описание номера")
    is_available = models.BooleanField(default=True, verbose_name="Доступен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True)

    def __str__(self):
        return f"{self.hotel.name} - Номер {self.room_number} ({self.get_room_type_display()})"

    def can_delete(self):
        """Проверка, можно ли удалить номер"""
        active_bookings = self.bookings.filter(
            status__in=['pending', 'confirmed', 'checked_in']
        )
        return not active_bookings.exists()

    def get_active_bookings(self):
        """Получить активные бронирования номера"""
        return self.bookings.filter(
            status__in=['pending', 'confirmed', 'checked_in']
        )

    def get_active_bookings_count(self):
        """Количество активных бронирований"""
        return self.bookings.filter(
            status__in=['pending', 'confirmed', 'checked_in']
        ).count()

    def get_delete_warning(self):
        """Получить предупреждение при удалении"""
        if self.bookings.exists():
            active_bookings = self.bookings.filter(status__in=['pending', 'confirmed', 'checked_in'])
            if active_bookings.exists():
                return f"На номер есть {active_bookings.count()} активных бронирований. Удаление невозможно."
        return None

    class Meta:
        verbose_name = "Номер"
        verbose_name_plural = "Номера"
        unique_together = ['hotel', 'room_number']
        ordering = ['hotel__name', 'room_number']

class Guest(models.Model):
    """Модель гостя (расширение пользователя)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guest_profile', verbose_name="Пользователь")
    phone = models.CharField(max_length=20, verbose_name="Телефон", null=True,)
    passport_number = models.CharField(max_length=20, blank=True, verbose_name="Номер паспорта")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    loyalty_points = models.IntegerField(default=0, verbose_name="Бонусные баллы")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    class Meta:
        verbose_name = "Гость"
        verbose_name_plural = "Гости"
        ordering = ['user__username']

class Service(models.Model):
    """Модель дополнительной услуги"""
    name = models.CharField(max_length=200, verbose_name="Название услуги")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    hotels = models.ManyToManyField(Hotel, related_name='services', blank=True, verbose_name="Отели")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def __str__(self):
        return f"{self.name} - {self.price} руб."

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ['name']

class Booking(models.Model):
    """Модель бронирования"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('checked_in', 'Заселен'),
        ('checked_out', 'Выселен'),
        ('cancelled', 'Отменено'),
    ]

    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='bookings', verbose_name="Гость", null=True,)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings', verbose_name="Номер")
    services = models.ManyToManyField(Service, related_name='bookings', blank=True, verbose_name="Дополнительные услуги")
    check_in_date = models.DateField(verbose_name="Дата заезда")
    check_out_date = models.DateField(verbose_name="Дата выезда")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Итоговая цена")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    special_requests = models.TextField(blank=True, verbose_name="Особые пожелания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True,)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def clean(self):
        """Валидация дат"""
        if self.check_in_date and self.check_out_date:
            if self.check_in_date >= self.check_out_date:
                raise ValidationError("Дата заезда должна быть раньше даты выезда")
            if self.check_in_date < timezone.now().date():
                raise ValidationError("Дата заезда не может быть в прошлом")

    def save(self, *args, **kwargs):
        """Автоматический расчет итоговой цены"""
        if not self.total_price and self.room and self.check_in_date and self.check_out_date:
            nights = (self.check_out_date - self.check_in_date).days
            self.total_price = self.room.price_per_night * nights
            # Добавляем стоимость услуг
            if self.pk and self.services.exists():
                services_price = self.services.aggregate(total=models.Sum('price'))['total'] or 0
                self.total_price += services_price
        super().save(*args, **kwargs)

    def can_cancel(self):
        """Проверка, можно ли отменить бронирование"""
        return self.status in ['pending', 'confirmed']

    def __str__(self):
        return f"Бронь {self.guest.user.username} - {self.room} ({self.check_in_date} - {self.check_out_date})"

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-created_at']

class Review(models.Model):
    """Модель отзыва"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews', verbose_name="Отель")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='reviews', verbose_name="Гость")
    rating = models.IntegerField(verbose_name="Рейтинг", choices=[(i, f"{i} звезд") for i in range(1, 6)])
    comment = models.TextField(verbose_name="Комментарий")
    advantages = models.TextField(blank=True, verbose_name="Достоинства")
    disadvantages = models.TextField(blank=True, verbose_name="Недостатки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отзыва", null=True,)
    is_verified = models.BooleanField(default=False, verbose_name="Подтвержден")

    def __str__(self):
        return f"Отзыв от {self.guest.user.username} об отеле {self.hotel.name}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ['hotel', 'guest']
        ordering = ['-created_at']

class Payment(models.Model):
    """Модель платежа"""
    PAYMENT_STATUS = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачено'),
        ('failed', 'Ошибка'),
        ('refunded', 'Возврат'),
    ]

    PAYMENT_METHOD = [
        ('card', 'Банковская карта'),
        ('cash', 'Наличные'),
        ('online', 'Онлайн перевод'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment', verbose_name="Бронирование")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, verbose_name="Способ оплаты")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending', verbose_name="Статус")
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name="ID транзакции")
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата оплаты")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True,)

    def __str__(self):
        return f"Платеж {self.amount} руб. для брони #{self.booking.id}"

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ['-created_at']
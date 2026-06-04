from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Пользователь'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        # Возвращаем полное имя или username
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.username})"
        elif self.first_name:
            return f"{self.first_name} ({self.username})"
        else:
            return self.username

    def get_full_name_display(self):
        """Возвращает полное имя для отображения"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username

    def is_manager(self):
        return self.role == 'manager' or self.role == 'admin'

    def is_admin(self):
        return self.role == 'admin'


class Hotel(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название отеля")
    address = models.TextField(verbose_name="Адрес")
    city = models.CharField(max_length=100, verbose_name="Город")
    description = models.TextField(verbose_name="Описание", blank=True)
    stars = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Звезды")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")
    website = models.URLField(blank=True, null=True, verbose_name="Веб-сайт")
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name="URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Отель"
        verbose_name_plural = "Отели"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(f"{self.name}-{self.city}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'★' * self.stars})"


class Room(models.Model):
    ROOM_TYPES = (
        ('single', 'Одноместный'),
        ('double', 'Двухместный'),
        ('twin', 'Двухместный с двумя кроватями'),
        ('suite', 'Люкс'),
        ('family', 'Семейный'),
    )

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms', verbose_name="Отель")
    room_number = models.CharField(max_length=10, verbose_name="Номер комнаты")
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, verbose_name="Тип номера")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за ночь")
    capacity = models.IntegerField(verbose_name="Вместимость")
    description = models.TextField(verbose_name="Описание", blank=True)
    is_available = models.BooleanField(default=True, verbose_name="Доступен")
    amenities = models.TextField(verbose_name="Удобства", blank=True, help_text="Через запятую")

    class Meta:
        verbose_name = "Номер"
        verbose_name_plural = "Номера"
        unique_together = ['hotel', 'room_number']

    def __str__(self):
        return f"{self.hotel.name} - {self.room_number} ({self.get_room_type_display()})"


class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', verbose_name="Пользователь")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', verbose_name="Номер")
    check_in = models.DateField(verbose_name="Дата заезда")
    check_out = models.DateField(verbose_name="Дата выезда")
    guests_count = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Количество гостей")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая стоимость")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    special_requests = models.TextField(blank=True, verbose_name="Особые пожелания")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-created_at']

    def get_nights_count(self):
        """Возвращает количество ночей"""
        if self.check_in and self.check_out:
            return (self.check_out - self.check_in).days
        return 0

    def get_services_total(self):
        """Возвращает общую стоимость услуг"""
        from django.db.models import Sum, F
        total = self.services.aggregate(
            total=Sum(F('quantity') * F('price_at_time'))
        )['total']
        return total or 0

    def get_room_total(self):
        """Возвращает стоимость номера за все ночи"""
        nights = (self.check_out - self.check_in).days
        if nights <= 0:
            nights = 1
        return nights * self.room.price_per_night

    @property
    def has_payment(self):
        """Проверяет, есть ли платеж"""
        return hasattr(self, 'payment_rel')

    @property
    def payment(self):
        """Возвращает платеж, если он есть"""
        try:
            return self.payment_record
        except Payment.DoesNotExist:
            return None



    def __str__(self):
        return f"Бронь #{self.id} - {self.user.username} - {self.room}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="Пользователь")
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews', verbose_name="Отель")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Оценка")
    comment = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ['user', 'hotel']

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.hotel.name} - {self.rating}★"


class Payment(models.Model):
    PAYMENT_METHODS = (
        ('card', 'Банковская карта'),
        ('cash', 'Наличные'),
        ('online', 'Онлайн'),
    )

    PAYMENT_STATUS = (
        ('pending', 'В ожидании'),
        ('completed', 'Завершен'),
        ('failed', 'Неудачный'),
        ('refunded', 'Возвращен'),
    )

    booking = models.OneToOneField(
        'Booking',
        on_delete=models.CASCADE,
        related_name='payment_record',
        unique=True,  # Добавьте unique=True
        verbose_name="Бронирование"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, verbose_name="Способ оплаты")
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending', verbose_name="Статус")
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, verbose_name="ID транзакции")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата оплаты")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Автоматически генерируем transaction_id если его нет
        if not self.transaction_id:
            import hashlib
            import time
            transaction_str = f"TRX{self.booking.id}{int(time.time())}{self.booking.user.id}"
            self.transaction_id = hashlib.md5(transaction_str.encode()).hexdigest()[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Платеж #{self.id} - Бронь #{self.booking.id} - {self.amount} ₽"


class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название услуги")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return f"{self.name} - {self.price}₽"


class BookingService(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='services', verbose_name="Бронирование")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings', verbose_name="Услуга")
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Количество")
    price_at_time = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена на момент заказа")

    class Meta:
        verbose_name = "Услуга бронирования"
        verbose_name_plural = "Услуги бронирования"
        unique_together = ['booking', 'service']

    def get_total(self):
        """Возвращает общую стоимость услуги"""
        return self.quantity * self.price_at_time

    @property
    def payment(self):
        """Возвращает платеж, если он есть"""
        try:
            return self.payment_rel
        except Payment.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.booking} - {self.service.name} x{self.quantity}"



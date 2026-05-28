from django.contrib import admin
from .models import Hotel, Room, Guest, Service, Booking, Review, Payment


class RoomInline(admin.TabularInline):
    """Inline отображение номеров в отеле"""
    model = Room
    extra = 1
    fields = ['room_number', 'room_type', 'price_per_night', 'capacity', 'is_available']


class ServiceInline(admin.TabularInline):
    """Inline отображение услуг в отеле"""
    model = Service.hotels.through
    extra = 1


class BookingInline(admin.TabularInline):
    """Inline отображение бронирований"""
    model = Booking
    extra = 0
    fields = ['guest', 'room', 'check_in_date', 'check_out_date', 'status']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    """Настройка админки для отеля"""
    list_display = ['name', 'address', 'stars', 'phone', 'email', 'created_at']
    list_filter = ['stars', 'created_at']
    search_fields = ['name', 'address']
    inlines = [RoomInline, ServiceInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'address', 'description', 'stars')
        }),
        ('Контактная информация', {
            'fields': ('phone', 'email')
        }),
        ('Время работы', {
            'fields': ('check_in_time', 'check_out_time')
        }),
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Настройка админки для номера"""
    list_display = ['room_number', 'hotel', 'room_type', 'price_per_night', 'capacity', 'is_available']
    list_filter = ['room_type', 'is_available', 'hotel']
    search_fields = ['room_number', 'hotel__name']
    list_editable = ['price_per_night', 'is_available']


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    """Настройка админки для гостя"""
    list_display = ['user', 'phone', 'loyalty_points', 'registration_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    list_filter = ['registration_date']
    readonly_fields = ['loyalty_points', 'registration_date']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Настройка админки для услуги"""
    list_display = ['name', 'price', 'is_active']
    list_filter = ['is_active', 'hotels']
    search_fields = ['name']
    list_editable = ['price', 'is_active']
    filter_horizontal = ['hotels']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Настройка админки для бронирования"""
    list_display = ['id', 'guest', 'room', 'check_in_date', 'check_out_date', 'total_price', 'status']
    list_filter = ['status', 'check_in_date', 'check_out_date']
    search_fields = ['guest__user__username', 'room__room_number']
    readonly_fields = ['total_price', 'created_at', 'updated_at']
    list_editable = ['status']
    filter_horizontal = ['services']

    fieldsets = (
        ('Основная информация', {
            'fields': ('guest', 'room', 'services')
        }),
        ('Даты', {
            'fields': ('check_in_date', 'check_out_date')
        }),
        ('Финансы', {
            'fields': ('total_price',)
        }),
        ('Статус', {
            'fields': ('status', 'special_requests')
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Настройка админки для отзыва"""
    list_display = ['hotel', 'guest', 'rating', 'is_verified', 'created_at']
    list_filter = ['rating', 'is_verified', 'created_at']
    search_fields = ['hotel__name', 'guest__user__username', 'comment']
    list_editable = ['is_verified']
    readonly_fields = ['created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Настройка админки для платежа"""
    list_display = ['booking', 'amount', 'payment_method', 'status', 'payment_date']
    list_filter = ['status', 'payment_method']
    search_fields = ['booking__guest__user__username', 'transaction_id']
    readonly_fields = ['created_at']
    list_editable = ['status']
from django.contrib import admin
from .models import User, Hotel, Room, Booking, Review, Payment, Service, BookingService

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_editable = ['role']

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'stars', 'phone', 'email', 'created_at']
    list_filter = ['city', 'stars', 'created_at']
    search_fields = ['name', 'city', 'address']
    prepopulated_fields = {'slug': ('name',)} if 'slug' in [f.name for f in Hotel._meta.get_fields()] else {}

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'hotel', 'room_type', 'price_per_night', 'capacity', 'is_available']
    list_filter = ['hotel', 'room_type', 'is_available']
    search_fields = ['room_number', 'hotel__name']
    list_editable = ['price_per_night', 'is_available']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'room', 'check_in', 'check_out', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'check_in', 'check_out', 'created_at']
    search_fields = ['user__username', 'room__room_number', 'room__hotel__name']
    list_editable = ['status']
    date_hierarchy = 'created_at'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'hotel', 'rating', 'comment', 'created_at']
    list_filter = ['rating', 'created_at', 'hotel']
    search_fields = ['user__username', 'hotel__name', 'comment']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'amount', 'payment_method', 'status', 'paid_at']
    list_filter = ['status', 'payment_method', 'paid_at']
    search_fields = ['booking__user__username', 'transaction_id']
    list_editable = ['status']
    raw_id_fields = ['booking']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['price', 'is_active']

@admin.register(BookingService)
class BookingServiceAdmin(admin.ModelAdmin):
    list_display = ['booking', 'service', 'quantity', 'price_at_time']
    list_filter = ['service']
    search_fields = ['booking__user__username', 'service__name']
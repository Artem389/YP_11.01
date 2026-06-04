# hotel_booking/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Основные страницы
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Отели
    path('hotels/', views.hotel_list_view, name='hotel_list'),
    path('hotels/search/', views.advanced_search_view, name='advanced_search'),
    path('hotels/<int:pk>/', views.hotel_detail_view, name='hotel_detail'),

    # Отзывы
    path('hotels/<int:hotel_id>/review/', views.review_create_view, name='review_create'),
    path('review/<int:pk>/edit/', views.review_edit_view, name='review_edit'),
    path('review/<int:pk>/delete/', views.review_delete_view, name='review_delete'),

    # Бронирования для пользователей
    path('booking/<int:room_id>/', views.booking_create_view, name='booking_create'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('booking/<int:booking_id>/add-service/', views.add_booking_service_view, name='add_booking_service'),

    # Платежи
    path('payment/<int:booking_id>/', views.payment_create_view, name='payment_create'),

    # ============ CRUD для менеджеров и админов ============
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # CRUD Hotels
    path('manage/hotels/', views.manage_hotels_view, name='manage_hotels'),
    path('manage/hotels/create/', views.hotel_create_view, name='hotel_create'),
    path('manage/hotels/<int:pk>/edit/', views.hotel_edit_view, name='hotel_edit'),
    path('manage/hotels/<int:pk>/delete/', views.hotel_delete_view, name='hotel_delete'),

    # CRUD Rooms
    path('manage/rooms/', views.manage_rooms_view, name='manage_rooms'),
    path('manage/rooms/create/', views.room_create_view, name='room_create'),
    path('manage/rooms/<int:pk>/edit/', views.room_edit_view, name='room_edit'),
    path('manage/rooms/<int:pk>/delete/', views.room_delete_view, name='room_delete'),

    # CRUD Bookings (для менеджера)
    path('manage/bookings/', views.manage_bookings_view, name='manage_bookings'),
    path('manage/bookings/<int:pk>/edit/', views.booking_edit_view, name='booking_edit'),
    path('manage/bookings/<int:pk>/delete/', views.booking_delete_view, name='booking_delete'),
    path('manage/bookings/<int:pk>/confirm/', views.booking_confirm_view, name='booking_confirm'),
    path('manage/bookings/<int:pk>/cancel/', views.booking_cancel_view, name='booking_cancel'),

    # CRUD Reviews
    path('manage/reviews/', views.manage_reviews_view, name='manage_reviews'),
    path('manage/reviews/<int:pk>/delete/', views.manage_review_delete_view, name='review_delete'),

    # CRUD Payments
    path('manage/payments/', views.manage_payments_view, name='manage_payments'),
    path('manage/payments/<int:pk>/edit/', views.payment_edit_view, name='payment_edit'),
    path('manage/payments/<int:pk>/delete/', views.payment_delete_view, name='payment_delete'),

    # CRUD Services
    path('manage/services/', views.manage_services_view, name='manage_services'),
    path('manage/services/create/', views.service_create_view, name='service_create'),
    path('manage/services/<int:pk>/edit/', views.service_edit_view, name='service_edit'),
    path('manage/services/<int:pk>/delete/', views.service_delete_view, name='service_delete'),

    # Управление пользователями (только админ)
    path('manage/users/', views.user_list_view, name='user_list'),
    path('manage/users/<int:pk>/role/', views.user_edit_role_view, name='user_edit_role'),
]
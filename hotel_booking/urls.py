# urls.py (внутри hotel_booking)

from django.urls import path
from . import views

urlpatterns = [
    # Главная и аутентификация
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Личный кабинет
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),

    # Поиск и фильтрация
    path('hotels/search/', views.hotel_search_view, name='hotel_search'),
    path('hotels/compare/', views.hotel_comparison_view, name='hotel_comparison'),

    # Избранное
    path('favorites/', views.favorites_view, name='favorites'),
    path('favorites/add/<int:hotel_id>/', views.add_favorite, name='add_favorite'),
    path('favorites/remove/<int:favorite_id>/', views.remove_favorite, name='remove_favorite'),

    # Оформление бронирования
    path('booking/checkout/', views.booking_checkout_view, name='booking_checkout'),
    path('booking/checkout/<int:hotel_id>/', views.booking_checkout_view, name='booking_checkout_hotel'),

    # Существующие маршруты для CRUD
    path('hotels/', views.HotelListView.as_view(), name='hotel_list'),
    path('hotels/<int:pk>/', views.HotelDetailView.as_view(), name='hotel_detail'),
    path('hotels/create/', views.HotelCreateView.as_view(), name='hotel_create'),
    path('hotels/<int:pk>/update/', views.HotelUpdateView.as_view(), name='hotel_update'),
    path('hotels/<int:pk>/delete/', views.HotelDeleteView.as_view(), name='hotel_delete'),

    # Rooms
    path('rooms/', views.RoomListView.as_view(), name='room_list'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('rooms/create/', views.RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/update/', views.RoomUpdateView.as_view(), name='room_update'),
    path('rooms/<int:pk>/delete/', views.RoomDeleteView.as_view(), name='room_delete'),

    # Guests
    path('guests/', views.GuestListView.as_view(), name='guest_list'),
    path('guests/<int:pk>/', views.GuestDetailView.as_view(), name='guest_detail'),
    path('guests/create/', views.GuestCreateView.as_view(), name='guest_create'),
    path('guests/<int:pk>/update/', views.GuestUpdateView.as_view(), name='guest_update'),
    path('guests/<int:pk>/delete/', views.GuestDeleteView.as_view(), name='guest_delete'),

    # Services
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('services/create/', views.ServiceCreateView.as_view(), name='service_create'),
    path('services/<int:pk>/update/', views.ServiceUpdateView.as_view(), name='service_update'),
    path('services/<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),

    # Bookings
    path('bookings/', views.BookingListView.as_view(), name='booking_list'),
    path('bookings/<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/create/', views.BookingCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/update/', views.BookingUpdateView.as_view(), name='booking_update'),
    path('bookings/<int:pk>/delete/', views.BookingDeleteView.as_view(), name='booking_delete'),

    # Reviews
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('reviews/create/<int:hotel_id>/', views.ReviewCreateView.as_view(), name='review_create'),
    path('reviews/<int:pk>/update/', views.ReviewUpdateView.as_view(), name='review_update'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),

    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/create/<int:booking_id>/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/update/', views.PaymentUpdateView.as_view(), name='payment_update'),
    path('payments/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),

    # Настройки профиля
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/security/', views.profile_security_view, name='profile_security'),
    path('profile/notifications/', views.profile_notifications_view, name='profile_notifications'),

    # Мои бронирования (дополнительные действия)
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('booking/<int:booking_id>/cancel/', views.booking_cancel_request, name='booking_cancel'),
    path('booking/<int:booking_id>/rebook/', views.booking_rebook_view, name='booking_rebook'),
    path('booking/<int:booking_id>/add-review/', views.booking_add_review, name='booking_add_review'),

# ========== Корзина ==========
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.cart_checkout_view, name='cart_checkout'),
]
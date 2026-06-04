from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'hotels', views.HotelViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'bookings', views.BookingViewSet)
router.register(r'reviews', views.ReviewViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'services', views.ServiceViewSet)
router.register(r'booking-services', views.BookingServiceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
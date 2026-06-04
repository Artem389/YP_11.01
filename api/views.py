from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from hotel_booking.models import User, Hotel, Room, Booking, Review, Payment, Service, BookingService
from .serializers import *
from .permissions import IsManagerOrAdmin, IsAdminOrReadOnly


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_queryset(self):
        if self.request.user.is_admin():
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'city', 'address']
    filterset_fields = ['city', 'stars']
    ordering_fields = ['stars', 'name', 'created_at']


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['hotel', 'room_type', 'is_available']
    search_fields = ['room_number']

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        room = self.get_object()
        bookings = room.bookings.filter(status='confirmed')
        return Response({'is_available': room.is_available, 'bookings_count': bookings.count()})


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'room', 'user']
    ordering_fields = ['check_in', 'check_out', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin() or user.is_manager():
            return Booking.objects.all()
        return Booking.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['hotel', 'rating']
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self):
        if self.request.user.is_admin():
            return Review.objects.all()
        return Review.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method']


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    filter_backends = [SearchFilter]
    search_fields = ['name']


class BookingServiceViewSet(viewsets.ModelViewSet):
    queryset = BookingService.objects.all()
    serializer_class = BookingServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
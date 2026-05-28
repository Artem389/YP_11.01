from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Hotel, Room, Guest, Service, Booking, Review, Payment


class HotelForm(forms.ModelForm):
    """Форма для отеля"""

    class Meta:
        model = Hotel
        fields = ['name', 'address', 'description', 'stars', 'phone', 'email', 'check_in_time', 'check_out_time']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'check_in_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'check_out_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'stars': forms.Select(attrs={'class': 'form-control'}),
        }


class RoomForm(forms.ModelForm):
    """Форма для номера"""

    class Meta:
        model = Room
        fields = ['hotel', 'room_number', 'room_type', 'price_per_night', 'capacity',
                  'square', 'has_wifi', 'has_tv', 'has_air_conditioning', 'description', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'square': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'hotel': forms.Select(attrs={'class': 'form-control'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
            'has_wifi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_tv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_air_conditioning': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_price_per_night(self):
        price = self.cleaned_data.get('price_per_night')
        if price and price <= 0:
            raise ValidationError("Цена должна быть больше нуля")
        return price

    def clean_room_number(self):
        room_number = self.cleaned_data.get('room_number')
        hotel = self.cleaned_data.get('hotel')
        if hotel and room_number:
            # Проверка уникальности номера в отеле
            existing = Room.objects.filter(hotel=hotel, room_number=room_number)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(f"Номер {room_number} уже существует в этом отеле")
        return room_number


class GuestForm(forms.ModelForm):
    """Форма для гостя"""

    class Meta:
        model = Guest
        fields = ['user', 'phone', 'passport_number', 'birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ServiceForm(forms.ModelForm):
    """Форма для услуги"""

    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'hotels', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'hotels': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 5}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise ValidationError("Цена должна быть больше нуля")
        return price


class BookingForm(forms.ModelForm):
    """Форма для бронирования"""

    class Meta:
        model = Booking
        fields = ['guest', 'room', 'services', 'check_in_date', 'check_out_date', 'special_requests']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'services': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 5}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'guest': forms.Select(attrs={'class': 'form-control'}),  # Добавлен выбор гостя
        }

    def __init__(self, *args, **kwargs):
        self.guest = kwargs.pop('guest', None)
        super().__init__(*args, **kwargs)
        # Фильтруем номера только доступные
        self.fields['room'].queryset = Room.objects.filter(is_available=True)
        # Добавляем всех гостей для выбора
        self.fields['guest'].queryset = Guest.objects.all()
        self.fields['guest'].required = True

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in_date')
        check_out = cleaned_data.get('check_out_date')
        room = cleaned_data.get('room')

        if check_in and check_out:
            if check_in >= check_out:
                raise ValidationError("Дата заезда должна быть раньше даты выезда")
            if check_in < timezone.now().date():
                raise ValidationError("Дата заезда не может быть в прошлом")

            # Проверка на пересечение с существующими бронированиями
            if room:
                conflicting_bookings = Booking.objects.filter(
                    room=room,
                    status__in=['pending', 'confirmed', 'checked_in'],
                    check_in_date__lt=check_out,
                    check_out_date__gt=check_in
                )
                if self.instance.pk:
                    conflicting_bookings = conflicting_bookings.exclude(pk=self.instance.pk)

                if conflicting_bookings.exists():
                    raise ValidationError("Номер уже забронирован на выбранные даты")

        return cleaned_data


class ReviewForm(forms.ModelForm):
    """Форма для отзыва"""

    class Meta:
        model = Review
        fields = ['rating', 'comment', 'advantages', 'disadvantages']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'advantages': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'disadvantages': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating and (rating < 1 or rating > 5):
            raise ValidationError("Рейтинг должен быть от 1 до 5")
        return rating


class PaymentForm(forms.ModelForm):
    """Форма для платежа"""

    class Meta:
        model = Payment
        fields = ['payment_method', 'transaction_id', 'status']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
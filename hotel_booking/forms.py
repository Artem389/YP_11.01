from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Hotel, Room, Guest, Service, Booking, Review, Payment
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django import forms
from .models import Guest, Favorite


class RegisterForm(UserCreationForm):
    """Форма регистрации"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # Создаем профиль гостя
            Guest.objects.create(
                user=user,
                phone=self.cleaned_data['phone']
            )
        return user


class LoginForm(AuthenticationForm):
    """Форма авторизации"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Имя пользователя'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class GuestProfileForm(forms.ModelForm):
    """Форма редактирования профиля гостя"""

    class Meta:
        model = Guest
        fields = ['phone', 'passport_number', 'birth_date', 'avatar']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


class FavoriteForm(forms.ModelForm):
    """Форма для избранного"""

    class Meta:
        model = Favorite
        fields = ['guest', 'hotel']


class SearchForm(forms.Form):
    """Форма поиска отелей"""
    destination = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Куда хотите поехать?',
        'class': 'search-input'
    }))
    check_in = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'form-control'
    }))
    check_out = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'form-control'
    }))
    guests = forms.IntegerField(required=False, min_value=1, initial=2, widget=forms.NumberInput(attrs={
        'class': 'form-control'
    }))
    min_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'от'
    }))
    max_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'до'
    }))
    stars = forms.MultipleChoiceField(required=False, choices=[(i, f"{i} звезд") for i in range(1, 6)],
                                      widget=forms.CheckboxSelectMultiple)
    amenities = forms.MultipleChoiceField(required=False, choices=[
        ('wifi', 'Бесплатный Wi-Fi'),
        ('parking', 'Парковка'),
        ('pool', 'Бассейн'),
        ('fitness', 'Фитнес-центр'),
        ('restaurant', 'Ресторан'),
    ], widget=forms.CheckboxSelectMultiple)


class HotelForm(forms.ModelForm):
    """Форма для отеля с улучшенными виджетами"""

    class Meta:
        model = Hotel
        fields = ['name', 'address', 'description', 'stars', 'phone', 'email', 'check_in_time', 'check_out_time']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название отеля'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Адрес'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание отеля'}),
            'stars': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (xxx) xxx-xx-xx'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.com'}),
            'check_in_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


class RoomForm(forms.ModelForm):
    """Форма для номера"""

    class Meta:
        model = Room
        fields = ['hotel', 'room_number', 'room_type', 'price_per_night', 'capacity',
                  'square', 'has_wifi', 'has_tv', 'has_air_conditioning', 'description', 'is_available']
        widgets = {
            'hotel': forms.Select(attrs={'class': 'form-select'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер комнаты'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'price_per_night': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Цена за ночь'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Вместимость'}),
            'square': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Площадь (м²)'}),
            'has_wifi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_tv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_air_conditioning': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание номера'}),
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

class CustomPasswordChangeForm(PasswordChangeForm):
    """Форма смены пароля"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
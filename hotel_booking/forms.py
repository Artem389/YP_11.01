from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Hotel, Room, Booking, Review, Payment, Service
import re


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким именем уже существует')
        if len(username) < 3:
            raise ValidationError('Имя пользователя должно содержать минимум 3 символа')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Простая валидация телефона
            phone_clean = re.sub(r'[^\d+]', '', phone)
            if len(phone_clean) < 10:
                raise ValidationError('Введите корректный номер телефона')
        return phone

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise ValidationError('Пароль должен содержать минимум 8 символов')
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError('Пароль должен содержать хотя бы одну букву')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Пароль должен содержать хотя бы одну цифру')
        return password


class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = ['name', 'address', 'city', 'description', 'stars', 'phone', 'email', 'website']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'stars': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def clean_stars(self):
        stars = self.cleaned_data.get('stars')
        if stars < 1 or stars > 5:
            raise ValidationError('Количество звезд должно быть от 1 до 5')
        return stars


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['hotel', 'room_number', 'room_type', 'price_per_night', 'capacity', 'description', 'is_available',
                  'amenities']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'amenities': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean_price_per_night(self):
        price = self.cleaned_data.get('price_per_night')
        if price <= 0:
            raise ValidationError('Цена должна быть больше 0')
        return price


class BookingForm(forms.ModelForm):
    check_in = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    check_out = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    class Meta:
        model = Booking
        fields = ['check_in', 'check_out', 'guests_count', 'special_requests']
        widgets = {
            'special_requests': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'guests_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if check_in and check_out:
            if check_in >= check_out:
                raise ValidationError('Дата выезда должна быть позже даты заезда')

            if check_in < timezone.now().date():
                raise ValidationError('Дата заезда не может быть в прошлом')

        return cleaned_data


class BookingEditForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['status', 'check_in', 'check_out', 'guests_count', 'special_requests']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_out': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'guests_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise ValidationError('Оценка должна быть от 1 до 5')
        return rating


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method', 'status']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поле amount только для чтения или убираем его
        if 'amount' in self.fields:
            self.fields['amount'].widget.attrs['readonly'] = True

class PaymentEditForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Способ оплаты'
    )
    status = forms.ChoiceField(
        choices=Payment.PAYMENT_STATUS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Статус платежа'
    )

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
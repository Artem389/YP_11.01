from django.db.models import Q, Avg, ProtectedError, Min
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Hotel, Room, Guest, Service, Booking, Review, Payment
from .forms import HotelForm, RoomForm, GuestForm, ServiceForm, BookingForm, ReviewForm, PaymentForm
import logging
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from .forms import AddToCartForm, CartItemUpdateForm, OrderCheckoutForm
from .models import Cart, CartItem
from django.db.models import Sum

logger = logging.getLogger(__name__)


# ========== Базовые классы с обработкой ошибок ==========

class BaseListView(ListView):
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = getattr(self, 'title', 'Список')
        context['create_url'] = getattr(self, 'create_url', None)
        context['detail_url_name'] = getattr(self, 'detail_url_name', None)
        context['update_url_name'] = getattr(self, 'update_url_name', None)
        context['delete_url_name'] = getattr(self, 'delete_url_name', None)
        context['search_fields'] = getattr(self, 'search_fields', [])
        context['table_headers'] = getattr(self, 'table_headers', [])
        context['model_name'] = self.model.__name__
        return context

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            search = self.request.GET.get('search')
            if search and hasattr(self, 'search_fields'):
                q_filter = Q()
                for field in self.search_fields:
                    q_filter |= Q(**{f"{field}__icontains": search})
                queryset = queryset.filter(q_filter)
            # Явная сортировка для пагинации
            if hasattr(self.model._meta, 'ordering') and self.model._meta.ordering:
                queryset = queryset.order_by(*self.model._meta.ordering)
            else:
                queryset = queryset.order_by('id')
            return queryset
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке данных')
            return self.model.objects.none()


class BaseCreateView(CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = getattr(self, 'form_title', 'Создание')
        context['cancel_url'] = getattr(self, 'cancel_url', reverse_lazy('home'))
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'{self.model._meta.verbose_name} успешно создан(а)')
            return response
        except IntegrityError as e:
            messages.error(self.request, 'Ошибка: такая запись уже существует')
            logger.error(f"IntegrityError in create: {str(e)}")
            return self.form_invalid(form)
        except ValidationError as e:
            for error in e.messages:
                messages.error(self.request, error)
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка при создании: {str(e)}')
            logger.error(f"Error in create: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class BaseUpdateView(UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = getattr(self, 'form_title', 'Редактирование')
        context['cancel_url'] = getattr(self, 'cancel_url', reverse_lazy('home'))
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'{self.model._meta.verbose_name} успешно обновлен(а)')
            return response
        except IntegrityError as e:
            messages.error(self.request, 'Ошибка: такая запись уже существует')
            logger.error(f"IntegrityError in update: {str(e)}")
            return self.form_invalid(form)
        except ValidationError as e:
            for error in e.messages:
                messages.error(self.request, error)
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка при обновлении: {str(e)}')
            logger.error(f"Error in update: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class BaseDeleteView(DeleteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = getattr(self, 'cancel_url', reverse_lazy('home'))
        context['object_name'] = self.model._meta.verbose_name
        context['object_repr'] = str(self.object)
        context['warning_message'] = getattr(self, 'warning_message', None)
        return context

    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.object.delete()
            messages.success(request, f'{self.model._meta.verbose_name} успешно удален(а)')
            return redirect(self.get_success_url())
        except ProtectedError as e:
            # Ошибка при удалении объекта, на который есть ссылки
            protected_objects = e.protected_objects
            objects_list = ', '.join([str(obj) for obj in protected_objects[:5]])
            if len(protected_objects) > 5:
                objects_list += f' и еще {len(protected_objects) - 5}'
            messages.error(
                request,
                f'Невозможно удалить {self.model._meta.verbose_name}. '
                f'Существуют связанные объекты: {objects_list}'
            )
            logger.warning(f"ProtectedError when deleting {self.model.__name__}: {protected_objects}")
            return redirect(self.get_success_url())
        except IntegrityError as e:
            messages.error(request, f'Ошибка целостности данных: {str(e)}')
            logger.error(f"IntegrityError in delete: {str(e)}")
            return redirect(self.get_success_url())
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            logger.error(f"Error in delete: {str(e)}")
            return redirect(self.get_success_url())


# views.py - добавляем новые views

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, Avg, Count, F
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from .forms import (
    RegisterForm, LoginForm, UserProfileForm, GuestProfileForm,
    SearchForm, FavoriteForm, BookingForm
)
from .models import Guest, Favorite, Hotel, Room, Booking, Review, Service
import json


# ========== Аутентификация ==========

def register_view(request):
    """Регистрация пользователя"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация успешно завершена.')
            return redirect('dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """Авторизация пользователя"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'С возвращением, {username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('home')


# ========== Личный кабинет ==========

@login_required
def dashboard_view(request):
    """Панель управления пользователя"""
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        guest = Guest.objects.create(user=request.user)

    # Статистика
    active_bookings = Booking.objects.filter(
        guest=guest,
        status__in=['pending', 'confirmed', 'checked_in'],
        check_out_date__gte=timezone.now().date()
    ).count()

    completed_bookings = Booking.objects.filter(
        guest=guest,
        status='checked_out'
    ).count()

    reviews_count = Review.objects.filter(guest=guest).count()

    # Ближайшие бронирования
    upcoming_bookings = Booking.objects.filter(
        guest=guest,
        status__in=['pending', 'confirmed'],
        check_in_date__gte=timezone.now().date()
    ).order_by('check_in_date')[:5]

    context = {
        'guest': guest,
        'active_bookings': active_bookings,
        'completed_bookings': completed_bookings,
        'reviews_count': reviews_count,
        'upcoming_bookings': upcoming_bookings,
        'loyalty_points': guest.loyalty_points,
    }

    return render(request, 'dashboard.html', context)


@login_required
def profile_edit_view(request):
    """Редактирование профиля"""
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        guest = Guest.objects.create(user=request.user)

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user)
        guest_form = GuestProfileForm(request.POST, request.FILES, instance=guest)

        if user_form.is_valid() and guest_form.is_valid():
            user_form.save()
            guest_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserProfileForm(instance=request.user)
        guest_form = GuestProfileForm(instance=guest)

    context = {
        'user_form': user_form,
        'guest_form': guest_form,
        'guest': guest,
    }

    return render(request, 'profile_edit.html', context)


# ========== Поиск и фильтрация отелей ==========

def hotel_search_view(request):
    """Страница поиска отелей"""
    hotels = Hotel.objects.all().annotate(
        avg_rating=Avg('reviews__rating'),
        reviews_count=Count('reviews'),
        min_price=Min('rooms__price_per_night')
    )

    # Применяем фильтры
    destination = request.GET.get('destination', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    stars_list = request.GET.getlist('stars')
    amenities_list = request.GET.getlist('amenities')

    # Поиск по названию или адресу
    if destination:
        hotels = hotels.filter(
            Q(name__icontains=destination) |
            Q(address__icontains=destination)
        )

    # Фильтр по звездам
    if stars_list:
        stars_int = [int(s) for s in stars_list]
        hotels = hotels.filter(stars__in=stars_int)

    # Фильтр по цене
    if min_price:
        hotels = hotels.filter(min_price__gte=min_price)
    if max_price:
        hotels = hotels.filter(min_price__lte=max_price)

    # Фильтр по удобствам
    if 'wifi' in amenities_list:
        hotels = hotels.filter(rooms__has_wifi=True)
    if 'fitness' in amenities_list:
        hotels = hotels.filter(services__name__icontains='фитнес')

    # Сортировка
    sort_by = request.GET.get('sort', 'popularity')
    if sort_by == 'price_asc':
        hotels = hotels.order_by('min_price')
    elif sort_by == 'price_desc':
        hotels = hotels.order_by('-min_price')
    elif sort_by == 'rating':
        hotels = hotels.order_by('-avg_rating')
    else:  # popularity
        hotels = hotels.order_by('-stars', '-avg_rating')

    # Пагинация
    from django.core.paginator import Paginator
    paginator = Paginator(hotels, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_count': hotels.count(),
        'current_sort': sort_by,
        'request': request,
    }

    return render(request, 'hotel_search.html', context)

# ========== Избранное ==========

@login_required
def favorites_view(request):
    """Страница избранного"""
    try:
        guest = request.user.guest_profile
        favorites = Favorite.objects.filter(guest=guest).select_related('hotel')
    except Guest.DoesNotExist:
        favorites = []

    context = {
        'favorites': favorites,
    }

    return render(request, 'favorites.html', context)


@login_required
def add_favorite(request, hotel_id):
    """Добавить отель в избранное"""
    try:
        guest = request.user.guest_profile
        hotel = get_object_or_404(Hotel, id=hotel_id)

        favorite, created = Favorite.objects.get_or_create(guest=guest, hotel=hotel)

        if created:
            messages.success(request, f'Отель "{hotel.name}" добавлен в избранное.')
        else:
            messages.info(request, f'Отель "{hotel.name}" уже в избранном.')

        return redirect(request.META.get('HTTP_REFERER', 'hotel_list'))
    except Guest.DoesNotExist:
        messages.warning(request, 'Пожалуйста, заполните профиль для добавления в избранное.')
        return redirect('profile_edit')


@login_required
def remove_favorite(request, favorite_id):
    """Удалить отель из избранного"""
    try:
        guest = request.user.guest_profile
        favorite = get_object_or_404(Favorite, id=favorite_id, guest=guest)
        hotel_name = favorite.hotel.name
        favorite.delete()
        messages.success(request, f'Отель "{hotel_name}" удален из избранного.')
    except Guest.DoesNotExist:
        messages.warning(request, 'Профиль не найден.')

    return redirect('favorites')


# ========== Оформление бронирования (пошаговое) ==========

@login_required
def booking_checkout_view(request, hotel_id=None, room_id=None):
    """Пошаговое оформление бронирования"""
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        messages.warning(request, 'Пожалуйста, заполните профиль для бронирования.')
        return redirect('profile_edit')

    step = request.GET.get('step', '1')

    # Шаг 1: Выбор номера
    if step == '1':
        hotels = Hotel.objects.all()
        rooms = Room.objects.filter(is_available=True)

        if hotel_id:
            rooms = rooms.filter(hotel_id=hotel_id)
        if room_id:
            request.session['selected_room_id'] = room_id
            return redirect('booking_checkout?step=2')

        context = {
            'hotels': hotels,
            'rooms': rooms,
            'step': 1,
        }
        return render(request, 'booking_checkout.html', context)

    # Шаг 2: Данные гостя
    elif step == '2':
        room_id = request.session.get('selected_room_id')
        if not room_id:
            messages.error(request, 'Пожалуйста, сначала выберите номер.')
            return redirect('booking_checkout?step=1')

        room = get_object_or_404(Room, id=room_id)

        if request.method == 'POST':
            # Сохраняем данные в сессию
            request.session['booking_data'] = {
                'check_in': request.POST.get('check_in'),
                'check_out': request.POST.get('check_out'),
                'guests_count': request.POST.get('guests_count'),
                'special_requests': request.POST.get('special_requests', ''),
            }
            return redirect('booking_checkout?step=3')

        context = {
            'room': room,
            'guest': guest,
            'step': 2,
        }
        return render(request, 'booking_checkout.html', context)

    # Шаг 3: Дополнительные услуги
    elif step == '3':
        room_id = request.session.get('selected_room_id')
        booking_data = request.session.get('booking_data', {})

        if not room_id or not booking_data:
            messages.error(request, 'Пожалуйста, заполните все предыдущие шаги.')
            return redirect('booking_checkout?step=1')

        room = get_object_or_404(Room, id=room_id)
        services = Service.objects.filter(is_active=True)

        if request.method == 'POST':
            selected_services = request.POST.getlist('services')
            request.session['selected_services'] = selected_services
            return redirect('booking_checkout?step=4')

        context = {
            'room': room,
            'services': services,
            'step': 3,
        }
        return render(request, 'booking_checkout.html', context)

    # Шаг 4: Оплата
    elif step == '4':
        room_id = request.session.get('selected_room_id')
        booking_data = request.session.get('booking_data', {})
        selected_services = request.session.get('selected_services', [])

        if not room_id or not booking_data:
            messages.error(request, 'Пожалуйста, заполните все предыдущие шаги.')
            return redirect('booking_checkout?step=1')

        room = get_object_or_404(Room, id=room_id)

        # Расчет стоимости
        check_in = timezone.datetime.strptime(booking_data['check_in'], '%Y-%m-%d').date()
        check_out = timezone.datetime.strptime(booking_data['check_out'], '%Y-%m-%d').date()
        nights = (check_out - check_in).days
        room_total = room.price_per_night * nights

        services_list = Service.objects.filter(id__in=selected_services)
        services_total = services_list.aggregate(total=Sum('price'))['total'] or 0

        total_price = room_total + services_total

        # Применяем бонусные баллы
        use_points = request.POST.get('use_points') == 'on'
        points_discount = 0

        if use_points and guest.loyalty_points > 0:
            max_discount = min(guest.loyalty_points, total_price)
            points_discount = max_discount
            total_price -= points_discount

        if request.method == 'POST':
            # Создаем бронирование
            booking = Booking.objects.create(
                guest=guest,
                room=room,
                check_in_date=check_in,
                check_out_date=check_out,
                total_price=total_price,
                status='pending',
                special_requests=booking_data.get('special_requests', '')
            )

            # Добавляем услуги
            booking.services.set(services_list)

            # Используем бонусные баллы
            if use_points and points_discount > 0:
                guest.use_points(points_discount)

            # Очищаем сессию
            request.session.pop('selected_room_id', None)
            request.session.pop('booking_data', None)
            request.session.pop('selected_services', None)

            messages.success(request, f'Бронирование #{booking.id} успешно создано!')
            return redirect('booking_detail', pk=booking.id)

        context = {
            'room': room,
            'services': services_list,
            'room_total': room_total,
            'services_total': services_total,
            'total_price': total_price,
            'points_discount': points_discount,
            'available_points': guest.loyalty_points,
            'nights': nights,
            'step': 4,
        }
        return render(request, 'booking_checkout.html', context)

    return redirect('booking_checkout?step=1')


# ========== Сравнение отелей ==========

def hotel_comparison_view(request):
    """Страница сравнения отелей"""
    hotel_ids = request.GET.getlist('hotels')

    if not hotel_ids:
        # Показываем популярные отели для сравнения по умолчанию
        hotels = Hotel.objects.all().order_by('-stars')[:3]
    else:
        hotels = Hotel.objects.filter(id__in=hotel_ids)

    # Собираем данные для сравнения
    comparison_data = []
    for hotel in hotels:
        min_room_price = hotel.rooms.aggregate(min_price=Min('price_per_night'))['min_price'] or 0
        amenities = []

        if hotel.rooms.filter(has_wifi=True).exists():
            amenities.append('Wi-Fi')
        if hotel.rooms.filter(has_tv=True).exists():
            amenities.append('Телевизор')
        if hotel.rooms.filter(has_air_conditioning=True).exists():
            amenities.append('Кондиционер')

        comparison_data.append({
            'hotel': hotel,
            'min_price': min_room_price,
            'avg_rating': hotel.reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
            'reviews_count': hotel.reviews.count(),
            'amenities': amenities,
            'has_pool': hotel.services.filter(name__icontains='бассейн').exists(),
            'has_spa': hotel.services.filter(name__icontains='spa').exists(),
            'has_restaurant': hotel.services.filter(name__icontains='ресторан').exists(),
        })

    context = {
        'comparison_data': comparison_data,
    }

    return render(request, 'hotel_comparison.html', context)


# ========== Мои бронирования ==========

@login_required
def my_bookings_view(request):
    """Страница с бронированиями пользователя"""
    try:
        guest = request.user.guest_profile

        status_filter = request.GET.get('status', 'all')

        bookings = Booking.objects.filter(guest=guest)

        if status_filter == 'upcoming':
            bookings = bookings.filter(
                check_in_date__gte=timezone.now().date(),
                status__in=['pending', 'confirmed']
            )
        elif status_filter == 'past':
            bookings = bookings.filter(check_out_date__lt=timezone.now().date())
        elif status_filter == 'cancelled':
            bookings = bookings.filter(status='cancelled')
        elif status_filter != 'all':
            bookings = bookings.filter(status=status_filter)

        bookings = bookings.order_by('-created_at')

        context = {
            'bookings': bookings,
            'current_filter': status_filter,
        }
    except Guest.DoesNotExist:
        context = {'bookings': []}

    return render(request, 'my_bookings.html', context)

# ========== Главная страница ==========

def home(request):
    try:
        popular_hotels = Hotel.objects.all().order_by('-stars')[:3]
        context = {
            'popular_hotels': popular_hotels,
            'hotels_count': Hotel.objects.count(),
            'rooms_count': Room.objects.count(),
            'bookings_count': Booking.objects.count(),
            'reviews_count': Review.objects.count(),
            'now': timezone.now(),
        }
        return render(request, 'home.html', context)
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        messages.error(request, 'Ошибка при загрузке главной страницы')
        return render(request, 'home.html', {})


# ========== Hotel CRUD ==========

class HotelListView(BaseListView):
    model = Hotel
    template_name = 'hotel_list.html'
    title = 'Отели'
    create_url = reverse_lazy('hotel_create')
    detail_url_name = 'hotel_detail'
    update_url_name = 'hotel_update'
    delete_url_name = 'hotel_delete'
    search_fields = ['name', 'address']
    table_headers = ['Название', 'Адрес', 'Звезды', 'Рейтинг']

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            queryset = queryset.annotate(avg_rating=Avg('reviews__rating'))
            return queryset.order_by('-stars', 'name')
        except Exception as e:
            logger.error(f"Error in HotelListView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке списка отелей')
            return Hotel.objects.none()


class HotelDetailView(DetailView):
    model = Hotel
    template_name = 'hotel_detail.html'
    context_object_name = 'hotel'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем комнаты отеля в контекст
        context['rooms'] = self.object.rooms.filter(is_available=True)
        return context

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Hotel.DoesNotExist:
            messages.error(self.request, 'Отель не найден')
            return None
        except Exception as e:
            logger.error(f"Error in HotelDetailView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке отеля')
            return None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            return redirect('hotel_search')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class HotelCreateView(BaseCreateView):
    model = Hotel
    form_class = HotelForm
    template_name = 'hotel_form.html'
    success_url = reverse_lazy('hotel_list')
    cancel_url = reverse_lazy('hotel_list')
    form_title = 'Создание отеля'


class HotelUpdateView(BaseUpdateView):
    model = Hotel
    form_class = HotelForm
    template_name = 'hotel_form.html'
    success_url = reverse_lazy('hotel_list')
    cancel_url = reverse_lazy('hotel_list')
    form_title = 'Редактирование отеля'


class HotelDeleteView(BaseDeleteView):
    model = Hotel
    template_name = 'hotel_confirm_delete.html'
    success_url = reverse_lazy('hotel_list')
    cancel_url = reverse_lazy('hotel_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('hotel_list')
        context['object_name'] = 'Отель'
        context['object_repr'] = str(self.object)

        # Проверяем, можно ли удалить отель
        if self.object.rooms.exists():
            rooms_count = self.object.rooms.count()
            bookings_count = Booking.objects.filter(room__hotel=self.object).count()
            context[
                'warning_message'] = f'В отеле есть {rooms_count} номер(ов) и {bookings_count} бронирование(й). Удаление невозможно, пока есть номера.'
            context['cannot_delete'] = True
        else:
            context['warning_message'] = 'Внимание! Все номера этого отеля также будут удалены.'
            context['cannot_delete'] = False

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Проверка перед удалением
        if self.object.rooms.exists():
            messages.error(
                request,
                f'Невозможно удалить отель "{self.object.name}". '
                f'Сначала удалите все номера в этом отеле.'
            )
            return redirect('hotel_detail', pk=self.object.pk)

        return self.delete(request, *args, **kwargs)

# ========== Room CRUD ==========

class RoomListView(BaseListView):
    model = Room
    template_name = 'room_list.html'
    title = 'Номера'
    create_url = reverse_lazy('room_create')
    detail_url_name = 'room_detail'
    update_url_name = 'room_update'
    delete_url_name = 'room_delete'
    search_fields = ['room_number', 'hotel__name']
    table_headers = ['Отель', 'Номер', 'Тип', 'Цена за ночь', 'Вместимость']

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            return queryset.order_by('hotel__name', 'room_number')
        except Exception as e:
            logger.error(f"Error in RoomListView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке списка номеров')
            return Room.objects.none()


class RoomDetailView(DetailView):
    model = Room
    template_name = 'room_detail.html'
    context_object_name = 'room'

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Room.DoesNotExist:
            messages.error(self.request, 'Номер не найден')
            return None
        except Exception as e:
            logger.error(f"Error in RoomDetailView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке номера')
            return None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            return redirect('room_list')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class RoomCreateView(BaseCreateView):
    model = Room
    form_class = RoomForm
    template_name = 'room_form.html'
    success_url = reverse_lazy('room_list')
    cancel_url = reverse_lazy('room_list')
    form_title = 'Создание номера'


class RoomUpdateView(BaseUpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'room_form.html'
    success_url = reverse_lazy('room_list')
    cancel_url = reverse_lazy('room_list')
    form_title = 'Редактирование номера'


class RoomDeleteView(BaseDeleteView):
    model = Room
    template_name = 'room_confirm_delete.html'
    success_url = reverse_lazy('room_list')
    cancel_url = reverse_lazy('room_list')
    warning_message = 'Все бронирования этого номера будут отменены.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('room_list')
        context['object_name'] = 'Номер'
        context['object_repr'] = f"{self.object.hotel.name} - Номер {self.object.room_number}"

        # Проверяем активные бронирования
        active_bookings = self.object.bookings.filter(
            status__in=['pending', 'confirmed', 'checked_in']
        )
        completed_bookings = self.object.bookings.filter(
            status__in=['checked_out', 'cancelled']
        )

        if active_bookings.exists():
            context['cannot_delete'] = True
            context['warning_message'] = (
                f'Невозможно удалить номер. '
                f'У номера есть {active_bookings.count()} активных бронирований.\n'
                f'Сначала отмените или завершите эти бронирования.'
            )
            # Показываем список активных бронирований
            context['active_bookings'] = active_bookings
        else:
            context['cannot_delete'] = False
            if completed_bookings.exists():
                context['warning_message'] = (
                    f'У номера есть {completed_bookings.count()} завершенных бронирований. '
                    f'Номер не будет удален.'
                )

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Проверка на активные бронирования
        active_bookings = self.object.bookings.filter(
            status__in=['pending', 'confirmed', 'checked_in']
        )

        if active_bookings.exists():
            messages.error(
                request,
                f'Невозможно удалить номер "{self.object.room_number}" в отеле "{self.object.hotel.name}".\n'
                f'У номера есть {active_bookings.count()} активных бронирований.\n'
                f'Сначала отмените бронирования:'
            )
            # Выводим список активных бронирований
            for booking in active_bookings:
                messages.error(
                    request,
                    f'  - Бронь #{booking.id}: {booking.guest.user.username} '
                    f'({booking.check_in_date} - {booking.check_out_date})'
                )
            return redirect('room_detail', pk=self.object.pk)

        # Если нет активных бронирований, удаляем
        try:
            # Сохраняем информацию для сообщения
            room_info = str(self.object)
            self.object.delete()
            messages.success(request, f'Номер "{room_info}" успешно удален.')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении номера: {str(e)}')
            return redirect('room_detail', pk=self.object.pk)

        return redirect(self.get_success_url())

# ========== Guest CRUD ==========

class GuestListView(BaseListView):
    model = Guest
    template_name = 'guest_list.html'
    title = 'Гости'
    create_url = reverse_lazy('guest_create')
    detail_url_name = 'guest_detail'
    update_url_name = 'guest_update'
    delete_url_name = 'guest_delete'
    search_fields = ['user__username', 'phone', 'passport_number']
    table_headers = ['Пользователь', 'Телефон', 'Паспорт', 'Бонусные баллы', 'Дата регистрации']

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            return queryset.order_by('user__username')
        except Exception as e:
            logger.error(f"Error in GuestListView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке списка гостей')
            return Guest.objects.none()


class GuestDetailView(DetailView):
    model = Guest
    template_name = 'guest_detail.html'
    context_object_name = 'guest'

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Guest.DoesNotExist:
            messages.error(self.request, 'Гость не найден')
            return None
        except Exception as e:
            logger.error(f"Error in GuestDetailView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке гостя')
            return None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            return redirect('guest_list')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class GuestCreateView(BaseCreateView):
    model = Guest
    form_class = GuestForm
    template_name = 'guest_form.html'
    success_url = reverse_lazy('guest_list')
    cancel_url = reverse_lazy('guest_list')
    form_title = 'Создание гостя'


class GuestUpdateView(BaseUpdateView):
    model = Guest
    form_class = GuestForm
    template_name = 'guest_form.html'
    success_url = reverse_lazy('guest_list')
    cancel_url = reverse_lazy('guest_list')
    form_title = 'Редактирование гостя'


class GuestDeleteView(BaseDeleteView):
    model = Guest
    template_name = 'guest_confirm_delete.html'
    success_url = reverse_lazy('guest_list')
    cancel_url = reverse_lazy('guest_list')
    warning_message = 'Все бронирования и отзывы этого гостя также будут удалены.'


# ========== Service CRUD ==========

class ServiceListView(BaseListView):
    model = Service
    template_name = 'service_list.html'
    title = 'Услуги'
    create_url = reverse_lazy('service_create')
    detail_url_name = 'service_detail'
    update_url_name = 'service_update'
    delete_url_name = 'service_delete'
    search_fields = ['name']
    table_headers = ['Название', 'Цена', 'Активна', 'Количество отелей']

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            return queryset.order_by('name')
        except Exception as e:
            logger.error(f"Error in ServiceListView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке списка услуг')
            return Service.objects.none()


class ServiceDetailView(DetailView):
    model = Service
    template_name = 'service_detail.html'
    context_object_name = 'service'

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Service.DoesNotExist:
            messages.error(self.request, 'Услуга не найдена')
            return None
        except Exception as e:
            logger.error(f"Error in ServiceDetailView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке услуги')
            return None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            return redirect('service_list')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class ServiceCreateView(BaseCreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'service_form.html'
    success_url = reverse_lazy('service_list')
    cancel_url = reverse_lazy('service_list')
    form_title = 'Создание услуги'


class ServiceUpdateView(BaseUpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'service_form.html'
    success_url = reverse_lazy('service_list')
    cancel_url = reverse_lazy('service_list')
    form_title = 'Редактирование услуги'


class ServiceDeleteView(BaseDeleteView):
    model = Service
    template_name = 'service_confirm_delete.html'
    success_url = reverse_lazy('service_list')
    cancel_url = reverse_lazy('service_list')


# ========== Booking CRUD ==========

class BookingListView(BaseListView):
    model = Booking
    template_name = 'booking_list.html'
    title = 'Бронирования'
    create_url = reverse_lazy('booking_create')
    detail_url_name = 'booking_detail'
    update_url_name = 'booking_update'
    delete_url_name = 'booking_delete'
    search_fields = ['guest__user__username', 'room__room_number', 'room__hotel__name']
    table_headers = ['Гость', 'Отель', 'Номер', 'Даты', 'Сумма', 'Статус']

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            return queryset.order_by('-created_at')
        except Exception as e:
            logger.error(f"Error in BookingListView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке списка бронирований')
            return Booking.objects.none()


class BookingDetailView(DetailView):
    model = Booking
    template_name = 'booking_detail.html'
    context_object_name = 'booking'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.object

        # Расчет количества ночей
        nights = (booking.check_out_date - booking.check_in_date).days
        room_total = booking.room.price_per_night * nights

        # Расчет стоимости услуг - используем Sum без models.
        services_total = booking.services.aggregate(total=Sum('price'))['total'] or 0

        context['nights'] = nights
        context['room_total'] = room_total
        context['services_total'] = services_total

        return context

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Booking.DoesNotExist:
            messages.error(self.request, 'Бронирование не найдено')
            return None
        except Exception as e:
            logger.error(f"Error in BookingDetailView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке бронирования')
            return None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            # Перенаправляем в зависимости от роли
            if hasattr(request.user, 'guest_profile'):
                role = request.user.guest_profile.role
                if role == 'guest':
                    return redirect('my_bookings')
            return redirect('booking_list')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class BookingCreateView(BaseCreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking_form.html'
    success_url = reverse_lazy('booking_list')
    cancel_url = reverse_lazy('booking_list')
    form_title = 'Создание бронирования'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['guest'] = None  # Убираем передачу guest, чтобы форма показывала выбор
        return kwargs

    def form_valid(self, form):
        try:
            # Проверка на пересечение дат
            check_in = form.cleaned_data.get('check_in_date')
            check_out = form.cleaned_data.get('check_out_date')
            room = form.cleaned_data.get('room')

            if check_in and check_out and room:
                if check_in >= check_out:
                    messages.error(self.request, 'Дата заезда должна быть раньше даты выезда')
                    return self.form_invalid(form)
                if check_in < timezone.now().date():
                    messages.error(self.request, 'Дата заезда не может быть в прошлом')
                    return self.form_invalid(form)

                # Проверка на конфликтующие бронирования
                conflicting = Booking.objects.filter(
                    room=room,
                    status__in=['pending', 'confirmed', 'checked_in'],
                    check_in_date__lt=check_out,
                    check_out_date__gt=check_in
                )
                if conflicting.exists():
                    messages.error(self.request, 'Номер уже забронирован на выбранные даты')
                    return self.form_invalid(form)

            messages.success(self.request, 'Бронирование успешно создано')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error in BookingCreateView: {str(e)}")
            messages.error(self.request, f'Ошибка при создании бронирования: {str(e)}')
            return self.form_invalid(form)


class BookingUpdateView(BaseUpdateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking_form.html'
    success_url = reverse_lazy('booking_list')
    cancel_url = reverse_lazy('booking_list')
    form_title = 'Редактирование бронирования'


class BookingDeleteView(BaseDeleteView):
    model = Booking
    template_name = 'booking_confirm_delete.html'
    success_url = reverse_lazy('my_bookings')  # Перенаправляем на "Мои бронирования"
    cancel_url = reverse_lazy('my_bookings')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('my_bookings')
        context['object_name'] = 'Бронирование'
        context['object_repr'] = f"Бронь #{self.object.id} - {self.object.guest.user.username}"

        # Проверка для обычного пользователя
        if hasattr(self.request.user, 'guest_profile'):
            is_admin_or_manager = self.request.user.guest_profile.role in ['admin', 'manager']
        else:
            is_admin_or_manager = False

        if self.object.status in ['checked_in', 'checked_out']:
            context['cannot_delete'] = True
            context['warning_message'] = 'Невозможно отменить бронирование, так как гость уже заселен или выселен.'
        elif self.object.status == 'cancelled':
            context['cannot_delete'] = True
            context['warning_message'] = 'Бронирование уже отменено.'
        else:
            context['cannot_delete'] = False
            context['warning_message'] = 'После отмены бронирования номер станет доступен для других гостей.'

        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Не удаляем, а меняем статус на cancelled
        if self.object.status in ['pending', 'confirmed']:
            self.object.status = 'cancelled'
            self.object.save()
            messages.success(request, f'Бронирование #{self.object.id} успешно отменено.')
        else:
            messages.error(request, f'Невозможно отменить бронирование в статусе "{self.object.get_status_display()}".')

        # Перенаправляем обычных пользователей на "Мои бронирования"
        if hasattr(self.request.user, 'guest_profile'):
            role = self.request.user.guest_profile.role
            if role == 'guest':
                return redirect('my_bookings')

        return redirect(self.get_success_url())


# ========== Review CRUD (доработанный) ==========

class ReviewListView(BaseListView):
    model = Review
    template_name = 'review_list.html'
    title = 'Отзывы'
    create_url = None
    detail_url_name = 'review_detail'
    update_url_name = 'review_update'
    delete_url_name = 'review_delete'
    search_fields = ['hotel__name', 'guest__user__username', 'comment']
    table_headers = ['Отель', 'Гость', 'Рейтинг', 'Комментарий', 'Статус']

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            return queryset.order_by('-created_at')
        except Exception as e:
            logger.error(f"Error in ReviewListView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке списка отзывов')
            return Review.objects.none()


class ReviewDetailView(DetailView):
    model = Review
    template_name = 'review_detail.html'
    context_object_name = 'review'


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """Создание отзыва — только для авторизованных гостей, которые завершили бронирование"""
    model = Review
    form_class = ReviewForm
    template_name = 'review_form.html'
    form_title = 'Написать отзыв'

    def dispatch(self, request, *args, **kwargs):
        """Проверка, может ли пользователь оставить отзыв"""
        hotel_id = self.kwargs.get('hotel_id')
        self.hotel = get_object_or_404(Hotel, id=hotel_id)

        if not request.user.is_authenticated:
            messages.warning(request, 'Пожалуйста, войдите в систему, чтобы оставить отзыв')
            return redirect('login')

        try:
            self.guest = request.user.guest_profile
        except Guest.DoesNotExist:
            messages.warning(request, 'Пожалуйста, заполните профиль перед написанием отзыва')
            return redirect('profile_edit')

        # Проверка: было ли у гостя завершенное бронирование в этом отеле
        has_completed_booking = Booking.objects.filter(
            guest=self.guest,
            room__hotel=self.hotel,
            status='checked_out'
        ).exists()

        if not has_completed_booking:
            messages.error(request,
                           'Вы можете оставить отзыв только после того, как завершится ваше бронирование в этом отеле.')
            return redirect('hotel_detail', pk=hotel_id)

        # Проверка: не оставлял ли уже отзыв
        if Review.objects.filter(guest=self.guest, hotel=self.hotel).exists():
            messages.warning(request, 'Вы уже оставляли отзыв на этот отель.')
            return redirect('hotel_detail', pk=hotel_id)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Отзыв об отеле "{self.hotel.name}"'
        context['cancel_url'] = reverse('hotel_detail', kwargs={'pk': self.hotel.id})
        context['hotel'] = self.hotel
        return context

    def form_valid(self, form):
        form.instance.hotel = self.hotel
        form.instance.guest = self.guest
        form.instance.is_verified = False  # Отзывы проходят модерацию
        messages.success(self.request, 'Спасибо за отзыв! Он будет опубликован после проверки модератором.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('hotel_detail', kwargs={'pk': self.hotel.id})


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'review_form.html'
    form_title = 'Редактирование отзыва'

    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()
        # Только автор отзыва или админ/менеджер могут редактировать
        try:
            guest = request.user.guest_profile
            if review.guest != guest and guest.role not in ['admin', 'manager']:
                messages.error(request, 'У вас нет прав для редактирования этого отзыва')
                return redirect('review_detail', pk=review.pk)
        except Guest.DoesNotExist:
            messages.error(request, 'Профиль не найден')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('review_detail', kwargs={'pk': self.object.pk})


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review
    template_name = 'review_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()
        try:
            guest = request.user.guest_profile
            if review.guest != guest and guest.role not in ['admin', 'manager']:
                messages.error(request, 'У вас нет прав для удаления этого отзыва')
                return redirect('review_detail', pk=review.pk)
        except Guest.DoesNotExist:
            pass  # Анонимный пользователь не может удалять
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('hotel_detail', kwargs={'pk': self.object.hotel.id})

# ========== Payment CRUD ==========

class PaymentListView(BaseListView):
    model = Payment
    template_name = 'payment_list.html'
    title = 'Платежи'
    create_url = None
    detail_url_name = 'payment_detail'
    update_url_name = 'payment_update'
    delete_url_name = 'payment_delete'
    search_fields = ['booking__guest__user__username', 'transaction_id']
    table_headers = ['Бронирование', 'Гость', 'Сумма', 'Способ', 'Статус', 'Дата']

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            return queryset.order_by('-created_at')
        except Exception as e:
            logger.error(f"Error in PaymentListView: {str(e)}")
            messages.error(self.request, 'Ошибка при загрузке списка платежей')
            return Payment.objects.none()


class PaymentDetailView(DetailView):
    model = Payment
    template_name = 'payment_detail.html'
    context_object_name = 'payment'


class PaymentCreateView(BaseCreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payment_form.html'
    cancel_url = reverse_lazy('payment_list')
    form_title = 'Создание платежа'

    def get_success_url(self):
        # После создания платежа возвращаемся на страницу бронирования
        booking_id = self.kwargs['booking_id']
        return reverse_lazy('booking_detail', kwargs={'pk': booking_id})

    def form_valid(self, form):
        try:
            booking = get_object_or_404(Booking, id=self.kwargs['booking_id'])

            # Проверка: не существует ли уже платеж для этого бронирования
            if Payment.objects.filter(booking=booking).exists():
                messages.error(self.request, 'Для этого бронирования уже существует платеж')
                return redirect('booking_detail', pk=booking.id)

            form.instance.booking = booking
            form.instance.amount = booking.total_price

            # Если статус платежа 'paid', обновляем статус бронирования
            if form.cleaned_data.get('status') == 'paid':
                booking.status = 'confirmed'
                booking.save()
                messages.success(self.request, 'Платеж подтвержден, бронирование подтверждено!')

            messages.success(self.request, 'Платеж успешно создан')
            return super().form_valid(form)
        except Booking.DoesNotExist:
            messages.error(self.request, 'Бронирование не найдено')
            return redirect('booking_list')
        except Exception as e:
            logger.error(f"Error in PaymentCreateView: {str(e)}")
            messages.error(self.request, f'Ошибка при создании платежа: {str(e)}')
            return self.form_invalid(form)


class PaymentUpdateView(BaseUpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payment_form.html'
    success_url = reverse_lazy('payment_list')
    cancel_url = reverse_lazy('payment_list')
    form_title = 'Редактирование платежа'


class PaymentDeleteView(BaseDeleteView):
    model = Payment
    template_name = 'payment_confirm_delete.html'
    success_url = reverse_lazy('payment_list')
    cancel_url = reverse_lazy('payment_list')


# ========== Настройки профиля ==========

@login_required
def profile_edit_view(request):
    """Редактирование профиля пользователя"""
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        guest = Guest.objects.create(user=request.user)

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user)
        guest_form = GuestProfileForm(request.POST, request.FILES, instance=guest)

        if user_form.is_valid() and guest_form.is_valid():
            user_form.save()
            guest_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile_edit')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserProfileForm(instance=request.user)
        guest_form = GuestProfileForm(instance=guest)

    context = {
        'user_form': user_form,
        'guest_form': guest_form,
        'guest': guest,
        'active_tab': 'profile',
    }

    return render(request, 'profile_settings.html', context)


@login_required
def profile_security_view(request):
    """Настройки безопасности (смена пароля)"""
    from .forms import CustomPasswordChangeForm

    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Обновляем сессию, чтобы пользователь не разлогинился
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('profile_security')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomPasswordChangeForm(request.user)

    context = {
        'form': form,
        'active_tab': 'security',
    }

    return render(request, 'profile_settings.html', context)


@login_required
def profile_notifications_view(request):
    """Настройки уведомлений"""
    if request.method == 'POST':
        # Сохраняем настройки уведомлений в сессию или в модель
        request.session['email_notifications'] = request.POST.get('email_notifications') == 'on'
        request.session['booking_reminders'] = request.POST.get('booking_reminders') == 'on'
        request.session['promo_offers'] = request.POST.get('promo_offers') == 'on'
        messages.success(request, 'Настройки уведомлений сохранены!')
        return redirect('profile_notifications')

    context = {
        'active_tab': 'notifications',
        'email_notifications': request.session.get('email_notifications', True),
        'booking_reminders': request.session.get('booking_reminders', True),
        'promo_offers': request.session.get('promo_offers', False),
    }

    return render(request, 'profile_settings.html', context)


# ========== Мои бронирования (расширенная версия) ==========

@login_required
def my_bookings_view(request):
    """Страница с бронированиями пользователя"""
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        guest = Guest.objects.create(user=request.user)

    # Получаем параметры фильтрации
    status_filter = request.GET.get('status', 'all')
    sort_by = request.GET.get('sort', '-created_at')

    bookings = Booking.objects.filter(guest=guest)

    # Применяем фильтр по статусу
    if status_filter == 'upcoming':
        bookings = bookings.filter(
            check_in_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        )
    elif status_filter == 'current':
        bookings = bookings.filter(
            check_in_date__lte=timezone.now().date(),
            check_out_date__gte=timezone.now().date(),
            status__in=['confirmed', 'checked_in']
        )
    elif status_filter == 'past':
        bookings = bookings.filter(check_out_date__lt=timezone.now().date())
    elif status_filter == 'cancelled':
        bookings = bookings.filter(status='cancelled')
    elif status_filter != 'all':
        bookings = bookings.filter(status=status_filter)

    # Применяем сортировку
    if sort_by == 'date_asc':
        bookings = bookings.order_by('check_in_date')
    elif sort_by == 'date_desc':
        bookings = bookings.order_by('-check_in_date')
    elif sort_by == 'price_asc':
        bookings = bookings.order_by('total_price')
    elif sort_by == 'price_desc':
        bookings = bookings.order_by('-total_price')
    else:
        bookings = bookings.order_by('-created_at')

    # Пагинация
    from django.core.paginator import Paginator
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Статистика по бронированиям
    stats = {
        'total': Booking.objects.filter(guest=guest).count(),
        'active': Booking.objects.filter(guest=guest, status__in=['pending', 'confirmed', 'checked_in']).count(),
        'completed': Booking.objects.filter(guest=guest, status='checked_out').count(),
        'cancelled': Booking.objects.filter(guest=guest, status='cancelled').count(),
    }

    context = {
        'page_obj': page_obj,
        'current_filter': status_filter,
        'current_sort': sort_by,
        'stats': stats,
        'guest': guest,
    }

    return render(request, 'my_bookings.html', context)


@login_required
def booking_cancel_request(request, booking_id):
    """Запрос на отмену бронирования"""
    booking = get_object_or_404(Booking, id=booking_id)

    # Проверяем, что бронирование принадлежит текущему пользователю
    try:
        if booking.guest.user != request.user:
            messages.error(request, 'У вас нет прав для отмены этого бронирования.')
            return redirect('my_bookings')
    except AttributeError:
        messages.error(request, 'Ошибка доступа.')
        return redirect('my_bookings')

    # Проверяем, можно ли отменить
    if booking.status in ['checked_in', 'checked_out']:
        messages.error(request, 'Невозможно отменить бронирование, так как вы уже заселены или выселены.')
    elif booking.status == 'cancelled':
        messages.info(request, 'Бронирование уже отменено.')
    else:
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, f'Бронирование #{booking.id} успешно отменено.')

    return redirect('my_bookings')


@login_required
def booking_rebook_view(request, booking_id):
    """Повторное бронирование (создание нового на основе старого)"""
    old_booking = get_object_or_404(Booking, id=booking_id)

    try:
        if old_booking.guest.user != request.user:
            messages.error(request, 'У вас нет прав для этого действия.')
            return redirect('my_bookings')
    except AttributeError:
        messages.error(request, 'Ошибка доступа.')
        return redirect('my_bookings')

    # Сохраняем данные в сессию для предзаполнения формы
    request.session['rebook_data'] = {
        'hotel_id': old_booking.room.hotel.id,
        'room_id': old_booking.room.id,
        'check_in': str(old_booking.check_in_date),
        'check_out': str(old_booking.check_out_date),
    }

    messages.info(request, 'Выберите новые даты для повторного бронирования.')
    return redirect('booking_checkout')


@login_required
def booking_add_review(request, booking_id):
    """Добавить отзыв на завершенное бронирование"""
    booking = get_object_or_404(Booking, id=booking_id)

    try:
        if booking.guest.user != request.user:
            messages.error(request, 'У вас нет прав для этого действия.')
            return redirect('my_bookings')
    except AttributeError:
        messages.error(request, 'Ошибка доступа.')
        return redirect('my_bookings')

    # Проверяем, что бронирование завершено
    if booking.status != 'checked_out':
        messages.warning(request, 'Вы можете оставить отзыв только после выезда из отеля.')
        return redirect('my_bookings')

    # Проверяем, нет ли уже отзыва
    if Review.objects.filter(guest=booking.guest, hotel=booking.room.hotel).exists():
        messages.warning(request, 'Вы уже оставляли отзыв на этот отель.')
        return redirect('my_bookings')

    return redirect('review_create', hotel_id=booking.room.hotel.id)


# ========== Декораторы для проверки ролей ==========

def role_required(allowed_roles):
    """Декоратор для проверки роли пользователя"""

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                guest = request.user.guest_profile
                if guest.role == 'admin' or guest.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                messages.error(request, 'У вас нет доступа к этой странице')
                return redirect('dashboard')
            except Guest.DoesNotExist:
                messages.error(request, 'Профиль не найден')
                return redirect('login')

        return wrapper

    return decorator


# ========== Функции для работы с корзиной ==========

def get_or_create_cart(guest):
    """Получить или создать корзину для гостя"""
    cart, created = Cart.objects.get_or_create(guest=guest)
    return cart


@login_required
def cart_view(request):
    """Просмотр корзины"""
    try:
        guest = request.user.guest_profile
        cart, created = Cart.objects.get_or_create(guest=guest)
        cart_items = cart.items.all().select_related('room', 'room__hotel')

        # Обработка POST запроса (обновление/удаление)
        if request.method == 'POST':
            # Удаление позиции
            if 'remove_item' in request.POST:
                item_id = request.POST.get('remove_item')
                try:
                    item = CartItem.objects.get(id=item_id, cart=cart)
                    item.delete()
                    messages.success(request, 'Позиция удалена из корзины')
                except CartItem.DoesNotExist:
                    messages.error(request, 'Позиция не найдена')
                return redirect('cart')

            # Обновление корзины (количество гостей)
            updated = False
            for item in cart_items:
                field_name = f'guests_count_{item.id}'
                if field_name in request.POST:
                    try:
                        new_count = int(request.POST.get(field_name))
                        if 1 <= new_count <= item.room.capacity:
                            if item.guests_count != new_count:
                                item.guests_count = new_count
                                item.save()
                                updated = True
                        else:
                            messages.warning(request,
                                             f'Для номера {item.room.room_number} максимальное количество гостей: {item.room.capacity}')
                    except (ValueError, TypeError):
                        pass

            if updated:
                messages.success(request, 'Корзина обновлена')
            elif 'update_cart' in request.POST:
                messages.info(request, 'Изменений не обнаружено')

            return redirect('cart')

        total_price = cart.get_total_price()
        max_points_use = min(guest.loyalty_points, int(total_price)) if total_price else 0

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'total_price': total_price,
            'loyalty_points': guest.loyalty_points,
            'max_points_use': max_points_use,
        }
        return render(request, 'cart.html', context)
    except Guest.DoesNotExist:
        messages.warning(request, 'Пожалуйста, заполните профиль')
        return redirect('profile_edit')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return render(request, 'cart.html', {'cart_items': [], 'total_price': 0})

@login_required
@require_http_methods(['POST'])
def add_to_cart(request):
    """Добавление номера в корзину"""
    try:
        guest = request.user.guest_profile
        form = AddToCartForm(request.POST)

        if form.is_valid():
            room_id = form.cleaned_data['room_id']
            check_in = form.cleaned_data['check_in_date']
            check_out = form.cleaned_data['check_out_date']
            guests_count = form.cleaned_data['guests_count']

            room = get_object_or_404(Room, id=room_id, is_available=True)

            # Проверка дат
            if check_in >= check_out:
                messages.error(request, 'Дата заезда должна быть раньше даты выезда')
                return redirect('hotel_detail', pk=room.hotel.id)

            if check_in < timezone.now().date():
                messages.error(request, 'Дата заезда не может быть в прошлом')
                return redirect('hotel_detail', pk=room.hotel.id)

            # Проверка на конфликт с существующими бронированиями
            conflicting = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed', 'checked_in'],
                check_in_date__lt=check_out,
                check_out_date__gt=check_in
            )
            if conflicting.exists():
                messages.error(request, 'Номер уже забронирован на выбранные даты')
                return redirect('hotel_detail', pk=room.hotel.id)

            # Получаем или создаем корзину
            cart, created = Cart.objects.get_or_create(guest=guest)

            # Добавляем или обновляем позицию
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                room=room,
                check_in_date=check_in,
                check_out_date=check_out,
                defaults={'guests_count': guests_count}
            )

            if not created:
                cart_item.guests_count = guests_count
                cart_item.save()
                messages.success(request, f'Количество гостей для номера {room.room_number} обновлено')
            else:
                messages.success(request, f'Номер {room.room_number} добавлен в корзину')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    except Guest.DoesNotExist:
        messages.warning(request, 'Пожалуйста, заполните профиль для бронирования')
        return redirect('profile_edit')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')

    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    """Удаление позиции из корзины"""
    try:
        guest = request.user.guest_profile
        cart = get_or_create_cart(guest)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        messages.success(request, 'Позиция удалена из корзины')
    except Guest.DoesNotExist:
        messages.warning(request, 'Профиль не найден')

    return redirect('cart')


@login_required
def cart_checkout_view(request):
    """Оформление заказа из корзины"""
    try:
        guest = request.user.guest_profile
        cart = get_or_create_cart(guest)
        cart_items = cart.items.all().select_related('room', 'room__hotel')

        if not cart_items:
            messages.warning(request, 'Ваша корзина пуста')
            return redirect('cart')

        if request.method == 'POST':
            form = OrderCheckoutForm(request.POST)
            if form.is_valid():
                special_requests = form.cleaned_data['special_requests']
                use_points = form.cleaned_data['use_loyalty_points']

                total_price = cart.get_total_price()
                points_discount = 0

                # Применяем бонусные баллы
                if use_points and guest.loyalty_points > 0:
                    points_discount = min(guest.loyalty_points, int(total_price))
                    total_price -= points_discount

                # Создаем бронирования из каждой позиции корзины
                bookings_created = []
                for item in cart_items:
                    # Проверяем, не забронирован ли уже номер
                    conflicting = Booking.objects.filter(
                        room=item.room,
                        status__in=['pending', 'confirmed', 'checked_in'],
                        check_in_date__lt=item.check_out_date,
                        check_out_date__gt=item.check_in_date
                    )
                    if conflicting.exists():
                        messages.error(request, f'Номер {item.room.room_number} уже забронирован на выбранные даты')
                        return redirect('cart')

                    # Рассчитываем стоимость для этой позиции
                    nights = (item.check_out_date - item.check_in_date).days
                    item_total = item.room.price_per_night * nights

                    # Пропорционально распределяем скидку по баллам
                    if points_discount > 0:
                        discount_share = int(
                            item_total / cart.get_total_price() * points_discount) if cart.get_total_price() > 0 else 0
                        item_total -= discount_share

                    booking = Booking.objects.create(
                        guest=guest,
                        room=item.room,
                        check_in_date=item.check_in_date,
                        check_out_date=item.check_out_date,
                        total_price=item_total,
                        status='pending',
                        special_requests=special_requests
                    )
                    bookings_created.append(booking)

                # Используем бонусные баллы
                if use_points and points_discount > 0:
                    guest.use_points(points_discount)

                # Очищаем корзину
                cart.clear()

                messages.success(request, f'Успешно оформлено {len(bookings_created)} бронирований!')
                if len(bookings_created) == 1:
                    return redirect('booking_detail', pk=bookings_created[0].id)
                return redirect('my_bookings')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
        else:
            form = OrderCheckoutForm()

        total_price = cart.get_total_price()
        max_points_use = min(guest.loyalty_points, int(total_price))

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'total_price': total_price,
            'loyalty_points': guest.loyalty_points,
            'max_points_use': max_points_use,
            'form': form,
        }
        return render(request, 'cart_checkout.html', context)
    except Guest.DoesNotExist:
        messages.warning(request, 'Пожалуйста, заполните профиль')
        return redirect('profile_edit')


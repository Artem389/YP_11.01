from django.db.models import Q, Avg, ProtectedError
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
        }
        return render(request, 'hotel_booking/home.html', context)
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        messages.error(request, 'Ошибка при загрузке главной страницы')
        return render(request, 'hotel_booking/home.html', {})


# ========== Hotel CRUD ==========

class HotelListView(BaseListView):
    model = Hotel
    template_name = 'hotel_booking/hotel_list.html'
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
    template_name = 'hotel_booking/hotel_detail.html'
    context_object_name = 'hotel'

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
            return redirect('hotel_list')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class HotelCreateView(BaseCreateView):
    model = Hotel
    form_class = HotelForm
    template_name = 'hotel_booking/hotel_form.html'
    success_url = reverse_lazy('hotel_list')
    cancel_url = reverse_lazy('hotel_list')
    form_title = 'Создание отеля'


class HotelUpdateView(BaseUpdateView):
    model = Hotel
    form_class = HotelForm
    template_name = 'hotel_booking/hotel_form.html'
    success_url = reverse_lazy('hotel_list')
    cancel_url = reverse_lazy('hotel_list')
    form_title = 'Редактирование отеля'


class HotelDeleteView(BaseDeleteView):
    model = Hotel
    template_name = 'hotel_booking/hotel_confirm_delete.html'
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
    template_name = 'hotel_booking/room_list.html'
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
    template_name = 'hotel_booking/room_detail.html'
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
    template_name = 'hotel_booking/room_form.html'
    success_url = reverse_lazy('room_list')
    cancel_url = reverse_lazy('room_list')
    form_title = 'Создание номера'


class RoomUpdateView(BaseUpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'hotel_booking/room_form.html'
    success_url = reverse_lazy('room_list')
    cancel_url = reverse_lazy('room_list')
    form_title = 'Редактирование номера'


class RoomDeleteView(BaseDeleteView):
    model = Room
    template_name = 'hotel_booking/room_confirm_delete.html'
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
    template_name = 'hotel_booking/guest_list.html'
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
    template_name = 'hotel_booking/guest_detail.html'
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
    template_name = 'hotel_booking/guest_form.html'
    success_url = reverse_lazy('guest_list')
    cancel_url = reverse_lazy('guest_list')
    form_title = 'Создание гостя'


class GuestUpdateView(BaseUpdateView):
    model = Guest
    form_class = GuestForm
    template_name = 'hotel_booking/guest_form.html'
    success_url = reverse_lazy('guest_list')
    cancel_url = reverse_lazy('guest_list')
    form_title = 'Редактирование гостя'


class GuestDeleteView(BaseDeleteView):
    model = Guest
    template_name = 'hotel_booking/guest_confirm_delete.html'
    success_url = reverse_lazy('guest_list')
    cancel_url = reverse_lazy('guest_list')
    warning_message = 'Все бронирования и отзывы этого гостя также будут удалены.'


# ========== Service CRUD ==========

class ServiceListView(BaseListView):
    model = Service
    template_name = 'hotel_booking/service_list.html'
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
    template_name = 'hotel_booking/service_detail.html'
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
    template_name = 'hotel_booking/service_form.html'
    success_url = reverse_lazy('service_list')
    cancel_url = reverse_lazy('service_list')
    form_title = 'Создание услуги'


class ServiceUpdateView(BaseUpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'hotel_booking/service_form.html'
    success_url = reverse_lazy('service_list')
    cancel_url = reverse_lazy('service_list')
    form_title = 'Редактирование услуги'


class ServiceDeleteView(BaseDeleteView):
    model = Service
    template_name = 'hotel_booking/service_confirm_delete.html'
    success_url = reverse_lazy('service_list')
    cancel_url = reverse_lazy('service_list')


# ========== Booking CRUD ==========

class BookingListView(BaseListView):
    model = Booking
    template_name = 'hotel_booking/booking_list.html'
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
    template_name = 'hotel_booking/booking_detail.html'
    context_object_name = 'booking'

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
            return redirect('booking_list')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class BookingCreateView(BaseCreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'hotel_booking/booking_form.html'
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
    template_name = 'hotel_booking/booking_form.html'
    success_url = reverse_lazy('booking_list')
    cancel_url = reverse_lazy('booking_list')
    form_title = 'Редактирование бронирования'


class BookingDeleteView(BaseDeleteView):
    model = Booking
    template_name = 'hotel_booking/booking_confirm_delete.html'
    success_url = reverse_lazy('booking_list')
    cancel_url = reverse_lazy('booking_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('booking_list')
        context['object_name'] = 'Бронирование'
        context['object_repr'] = f"Бронь #{self.object.id} - {self.object.guest.user.username}"

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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Не удаляем, а меняем статус на cancelled
        if self.object.status in ['pending', 'confirmed']:
            self.object.status = 'cancelled'
            self.object.save()
            messages.success(request, f'Бронирование #{self.object.id} успешно отменено.')
        else:
            messages.error(request, f'Невозможно отменить бронирование в статусе "{self.object.get_status_display()}".')

        return redirect(self.get_success_url())


# ========== Review CRUD ==========

class ReviewListView(BaseListView):
    model = Review
    template_name = 'hotel_booking/review_list.html'
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
    template_name = 'hotel_booking/review_detail.html'
    context_object_name = 'review'


class ReviewCreateView(BaseCreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'hotel_booking/review_form.html'
    cancel_url = reverse_lazy('review_list')
    form_title = 'Создание отзыва'

    def get_success_url(self):
        return reverse_lazy('review_list')

    def form_valid(self, form):
        try:
            form.instance.hotel_id = self.kwargs['hotel_id']

            # Проверка: может ли гость оставить отзыв (было ли у него бронирование в этом отеле)
            guest = form.instance.guest if form.instance.guest else None
            hotel = form.instance.hotel
            if guest and hotel:
                has_booking = Booking.objects.filter(
                    guest=guest,
                    room__hotel=hotel,
                    status='checked_out'
                ).exists()
                if not has_booking:
                    messages.warning(self.request, 'Вы можете оставить отзыв только после выезда из отеля')

            messages.success(self.request, 'Отзыв успешно создан')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error in ReviewCreateView: {str(e)}")
            messages.error(self.request, f'Ошибка при создании отзыва: {str(e)}')
            return self.form_invalid(form)


class ReviewUpdateView(BaseUpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'hotel_booking/review_form.html'
    success_url = reverse_lazy('review_list')
    cancel_url = reverse_lazy('review_list')
    form_title = 'Редактирование отзыва'


class ReviewDeleteView(BaseDeleteView):
    model = Review
    template_name = 'hotel_booking/review_confirm_delete.html'
    success_url = reverse_lazy('review_list')
    cancel_url = reverse_lazy('review_list')


# ========== Payment CRUD ==========

class PaymentListView(BaseListView):
    model = Payment
    template_name = 'hotel_booking/payment_list.html'
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
    template_name = 'hotel_booking/payment_detail.html'
    context_object_name = 'payment'


class PaymentCreateView(BaseCreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'hotel_booking/payment_form.html'
    cancel_url = reverse_lazy('payment_list')
    form_title = 'Создание платежа'

    def get_success_url(self):
        return reverse_lazy('payment_list')

    def form_valid(self, form):
        try:
            booking = get_object_or_404(Booking, id=self.kwargs['booking_id'])

            # Проверка: не существует ли уже платеж для этого бронирования
            if Payment.objects.filter(booking=booking).exists():
                messages.error(self.request, 'Для этого бронирования уже существует платеж')
                return self.form_invalid(form)

            form.instance.booking = booking
            form.instance.amount = booking.total_price

            messages.success(self.request, 'Платеж успешно создан')
            return super().form_valid(form)
        except Booking.DoesNotExist:
            messages.error(self.request, 'Бронирование не найдено')
            return redirect('payment_list')
        except Exception as e:
            logger.error(f"Error in PaymentCreateView: {str(e)}")
            messages.error(self.request, f'Ошибка при создании платежа: {str(e)}')
            return self.form_invalid(form)


class PaymentUpdateView(BaseUpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'hotel_booking/payment_form.html'
    success_url = reverse_lazy('payment_list')
    cancel_url = reverse_lazy('payment_list')
    form_title = 'Редактирование платежа'


class PaymentDeleteView(BaseDeleteView):
    model = Payment
    template_name = 'hotel_booking/payment_confirm_delete.html'
    success_url = reverse_lazy('payment_list')
    cancel_url = reverse_lazy('payment_list')
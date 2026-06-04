from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import User, Hotel, Room, Booking, Review, Payment, Service, BookingService
from .forms import *
from .decorators import role_required


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'hotel_booking/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = UserLoginForm()
    return render(request, 'hotel_booking/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('home')


def home_view(request):
    hotels = Hotel.objects.filter()[:6]
    return render(request, 'hotel_booking/home.html', {'hotels': hotels})


def hotel_list_view(request):
    hotels = Hotel.objects.all()
    query = request.GET.get('q')
    city = request.GET.get('city')
    stars = request.GET.get('stars')

    if query:
        hotels = hotels.filter(Q(name__icontains=query) | Q(city__icontains=query))
    if city:
        hotels = hotels.filter(city__icontains=city)
    if stars:
        hotels = hotels.filter(stars=stars)

    return render(request, 'hotel_booking/hotel_list.html', {'hotels': hotels})


def hotel_detail_view(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    rooms = hotel.rooms.filter(is_available=True)
    reviews = hotel.reviews.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    return render(request, 'hotel_booking/hotel_detail.html', {
        'hotel': hotel,
        'rooms': rooms,
        'reviews': reviews,
        'avg_rating': avg_rating
    })


@login_required
def booking_create_view(request, room_id):
    room = get_object_or_404(Room, pk=room_id)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.room = room
            check_in = form.cleaned_data['check_in']
            check_out = form.cleaned_data['check_out']
            nights = (check_out - check_in).days
            booking.total_price = nights * room.price_per_night
            booking.save()

            messages.success(request, 'Бронирование успешно создано!')
            return redirect('my_bookings')
    else:
        form = BookingForm()

    return render(request, 'hotel_booking/booking_form.html', {
        'form': form,
        'room': room
    })


@login_required
def my_bookings_view(request):
    bookings = request.user.bookings.all()
    return render(request, 'hotel_booking/my_bookings.html', {'bookings': bookings})


@role_required(['manager', 'admin'])
def manage_hotels_view(request):
    hotels = Hotel.objects.all()
    return render(request, 'hotel_booking/manage/hotels.html', {'hotels': hotels})


@role_required(['manager', 'admin'])
def hotel_create_view(request):
    if request.method == 'POST':
        form = HotelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Отель успешно создан!')
            return redirect('manage_hotels')
    else:
        form = HotelForm()
    return render(request, 'hotel_booking/manage/hotel_form.html', {'form': form})


@role_required(['manager', 'admin'])
def hotel_edit_view(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'POST':
        form = HotelForm(request.POST, instance=hotel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Отель успешно обновлен!')
            return redirect('manage_hotels')
    else:
        form = HotelForm(instance=hotel)
    return render(request, 'hotel_booking/manage/hotel_form.html', {'form': form, 'hotel': hotel})


@role_required(['manager', 'admin'])
def hotel_delete_view(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'POST':
        hotel.delete()
        messages.success(request, 'Отель успешно удален!')
        return redirect('manage_hotels')
    return render(request, 'hotel_booking/manage/hotel_confirm_delete.html', {'hotel': hotel})


# Аналогичные CRUD views для Room, Booking, Review, Payment, Service
# (создайте по аналогии для всех 7 сущностей)

@role_required(['admin'])
def user_list_view(request):
    users = User.objects.all()
    return render(request, 'hotel_booking/manage/users.html', {'users': users})


@role_required(['admin'])
def user_edit_role_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserRoleForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Роль пользователя обновлена!')
            return redirect('user_list')
    else:
        form = UserRoleForm(instance=user)
    return render(request, 'hotel_booking/manage/user_role_form.html', {'form': form, 'user': user})


# Добавьте эти функции в существующий views.py

# ============ CRUD для Room ============
@role_required(['manager', 'admin'])
def manage_rooms_view(request):
    rooms = Room.objects.all().select_related('hotel')
    return render(request, 'hotel_booking/manage/rooms.html', {'rooms': rooms})


@role_required(['manager', 'admin'])
def room_create_view(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Номер успешно создан!')
            return redirect('manage_rooms')
    else:
        form = RoomForm()
    return render(request, 'hotel_booking/manage/room_form.html', {'form': form})


@role_required(['manager', 'admin'])
def room_edit_view(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Номер успешно обновлен!')
            return redirect('manage_rooms')
    else:
        form = RoomForm(instance=room)
    return render(request, 'hotel_booking/manage/room_form.html', {'form': form, 'room': room})


@role_required(['manager', 'admin'])
def room_delete_view(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Номер успешно удален!')
        return redirect('manage_rooms')
    return render(request, 'hotel_booking/manage/room_confirm_delete.html', {'room': room})


# ============ CRUD для Booking (для менеджера) ============
@role_required(['manager', 'admin'])
def manage_bookings_view(request):
    bookings = Booking.objects.all().select_related('user', 'room', 'room__hotel')
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    return render(request, 'hotel_booking/manage/bookings.html', {'bookings': bookings})


@role_required(['manager', 'admin'])
def booking_edit_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        form = BookingEditForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирование успешно обновлено!')
            return redirect('manage_bookings')
    else:
        form = BookingEditForm(instance=booking)
    return render(request, 'hotel_booking/manage/booking_edit.html', {'form': form, 'booking': booking})


@role_required(['manager', 'admin'])
def booking_delete_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'Бронирование успешно удалено!')
        return redirect('manage_bookings')
    return render(request, 'hotel_booking/manage/booking_confirm_delete.html', {'booking': booking})


@role_required(['manager', 'admin'])
def booking_confirm_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    booking.status = 'confirmed'
    booking.save()
    messages.success(request, 'Бронирование подтверждено!')
    return redirect('manage_bookings')


@role_required(['manager', 'admin'])
def booking_cancel_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    booking.status = 'cancelled'
    booking.save()
    messages.success(request, 'Бронирование отменено!')
    return redirect('manage_bookings')


# ============ CRUD для Review ============
@role_required(['manager', 'admin'])
def manage_reviews_view(request):
    reviews = Review.objects.all().select_related('user', 'hotel')
    return render(request, 'hotel_booking/manage/reviews.html', {'reviews': reviews})


@login_required
def review_create_view(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)

    # Проверяем, не оставлял ли пользователь уже отзыв
    existing_review = Review.objects.filter(user=request.user, hotel=hotel).first()
    if existing_review:
        messages.warning(request, 'Вы уже оставляли отзыв на этот отель')
        return redirect('hotel_detail', pk=hotel_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.hotel = hotel
            review.save()
            messages.success(request, 'Спасибо за ваш отзыв!')
            return redirect('hotel_detail', pk=hotel_id)
    else:
        form = ReviewForm()

    return render(request, 'hotel_booking/review_form.html', {'form': form, 'hotel': hotel})


@role_required(['manager', 'admin'])
def review_delete_view(request, pk):
    review = get_object_or_404(Review, pk=pk)
    hotel_id = review.hotel.id
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Отзыв удален!')
        return redirect('manage_reviews')
    return render(request, 'hotel_booking/manage/review_confirm_delete.html', {'review': review})


@login_required
def review_edit_view(request, pk):
    review = get_object_or_404(Review, pk=pk)

    # Проверяем, что пользователь является автором отзыва или админом
    if review.user != request.user and not request.user.is_admin():
        messages.error(request, 'У вас нет прав на редактирование этого отзыва')
        return redirect('hotel_detail', pk=review.hotel.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ваш отзыв успешно обновлен!')
            return redirect('hotel_detail', pk=review.hotel.id)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'hotel_booking/review_edit.html', {
        'form': form,
        'review': review,
        'hotel': review.hotel
    })

@role_required(['manager', 'admin'])
def manage_review_delete_view(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Отзыв удален!')
        return redirect('manage_reviews')
    return render(request, 'hotel_booking/manage/review_confirm_delete.html', {'review': review})

# ============ CRUD для Payment ============
@role_required(['manager', 'admin'])
def manage_payments_view(request):
    payments = Payment.objects.all().select_related('booking', 'booking__user', 'booking__room')
    return render(request, 'hotel_booking/manage/payments.html', {'payments': payments})


@login_required
def payment_create_view(request, booking_id):
    from django.utils import timezone
    import hashlib

    booking = get_object_or_404(Booking, pk=booking_id)

    # Проверяем, что бронирование принадлежит пользователю
    if booking.user != request.user and not request.user.is_manager():
        messages.error(request, 'У вас нет доступа к этому платежу')
        return redirect('my_bookings')

    # Проверяем, есть ли уже платеж - ИСПРАВЛЕННАЯ ПРОВЕРКА
    try:
        existing_payment = Payment.objects.get(booking=booking)
        if existing_payment:
            messages.warning(request, 'Платеж для этого бронирования уже существует')
            return redirect('my_bookings')
    except Payment.DoesNotExist:
        pass  # Платежа нет, продолжаем

    # Проверяем статус бронирования
    if booking.status != 'pending':
        messages.warning(request, 'Оплата возможна только для бронирований в статусе "Ожидает"')
        return redirect('my_bookings')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        if payment_method:
            try:
                # Еще раз проверяем перед созданием
                if Payment.objects.filter(booking=booking).exists():
                    messages.warning(request, 'Платеж уже был создан')
                    return redirect('my_bookings')

                payment = Payment.objects.create(
                    booking=booking,
                    amount=booking.total_price,
                    payment_method=payment_method,
                    status='completed',
                    transaction_id=hashlib.md5(
                        f"TRX{booking.id}{int(timezone.now().timestamp())}{booking.user.id}".encode()).hexdigest()[
                        :16].upper(),
                    paid_at=timezone.now()
                )

                # Обновляем статус бронирования
                booking.status = 'confirmed'
                booking.save()

                messages.success(request, f'Оплата прошла успешно! Сумма: {payment.amount} ₽')
                return redirect('my_bookings')
            except Exception as e:
                messages.error(request, f'Ошибка при обработке платежа: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, выберите способ оплаты')

    return render(request, 'hotel_booking/payment_form.html', {
        'booking': booking
    })


@login_required
def payment_create_view(request, booking_id):
    from django.utils import timezone
    import hashlib

    booking = get_object_or_404(Booking, pk=booking_id)

    # Проверяем, что бронирование принадлежит пользователю
    if booking.user != request.user and not request.user.is_manager():
        messages.error(request, 'У вас нет доступа к этому платежу')
        return redirect('my_bookings')

    # Проверяем, есть ли уже платеж
    try:
        existing_payment = Payment.objects.get(booking=booking)
        if existing_payment:
            messages.warning(request, 'Платеж для этого бронирования уже существует')
            return redirect('my_bookings')
    except Payment.DoesNotExist:
        pass

    # Проверяем статус бронирования
    if booking.status != 'pending':
        messages.warning(request, 'Оплата возможна только для бронирований в статусе "Ожидает"')
        return redirect('my_bookings')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        if not payment_method:
            messages.error(request, 'Пожалуйста, выберите способ оплаты')
            return render(request, 'hotel_booking/payment_form.html', {'booking': booking})

        try:
            # Финальная проверка перед созданием
            if Payment.objects.filter(booking=booking).exists():
                messages.warning(request, 'Платеж уже был создан')
                return redirect('my_bookings')

            # Создаем платеж
            payment = Payment(
                booking=booking,
                amount=booking.total_price,
                payment_method=payment_method,
                status='completed',
                paid_at=timezone.now()
            )
            payment.save()

            # Обновляем статус бронирования
            booking.status = 'confirmed'
            booking.save()

            messages.success(request, f'Оплата прошла успешно! Сумма: {payment.amount} ₽')
            return redirect('my_bookings')

        except Exception as e:
            messages.error(request, f'Ошибка при обработке платежа: {str(e)}')
            return render(request, 'hotel_booking/payment_form.html', {'booking': booking})

    return render(request, 'hotel_booking/payment_form.html', {'booking': booking})


@role_required(['manager', 'admin'])
def payment_edit_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    # Загружаем связанные данные
    payment = Payment.objects.select_related('booking__user', 'booking__room__hotel').get(pk=pk)

    if request.method == 'POST':
        form = PaymentEditForm(request.POST)
        if form.is_valid():
            payment.payment_method = form.cleaned_data['payment_method']
            payment.status = form.cleaned_data['status']
            payment.save()
            messages.success(request, 'Платеж успешно обновлен!')
            return redirect('manage_payments')
    else:
        form = PaymentEditForm(initial={
            'payment_method': payment.payment_method,
            'status': payment.status
        })

    return render(request, 'hotel_booking/manage/payment_form.html', {
        'form': form,
        'payment': payment
    })


@role_required(['manager', 'admin'])
def payment_delete_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Платеж успешно удален!')
        return redirect('manage_payments')
    return render(request, 'hotel_booking/manage/payment_confirm_delete.html', {'payment': payment})

@role_required(['manager', 'admin'])
def payment_delete_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Платеж удален!')
        return redirect('manage_payments')
    return render(request, 'hotel_booking/manage/payment_confirm_delete.html', {'payment': payment})


# ============ CRUD для Service ============
@role_required(['manager', 'admin'])
def manage_services_view(request):
    services = Service.objects.all()
    return render(request, 'hotel_booking/manage/services.html', {'services': services})


@role_required(['manager', 'admin'])
def service_create_view(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Услуга успешно создана!')
            return redirect('manage_services')
    else:
        form = ServiceForm()
    return render(request, 'hotel_booking/manage/service_form.html', {'form': form})


@role_required(['manager', 'admin'])
def service_edit_view(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Услуга успешно обновлена!')
            return redirect('manage_services')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'hotel_booking/manage/service_form.html', {'form': form, 'service': service})


@role_required(['manager', 'admin'])
def service_delete_view(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Услуга успешно удалена!')
        return redirect('manage_services')
    return render(request, 'hotel_booking/manage/service_confirm_delete.html', {'service': service})


@login_required
def add_booking_service_view(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    # Проверяем, что бронирование принадлежит пользователю
    if booking.user != request.user and not request.user.is_manager():
        messages.error(request, 'У вас нет доступа к этому бронированию')
        return redirect('my_bookings')

    # Проверяем статус бронирования - только для неоплаченных
    if booking.status != 'pending':
        messages.warning(request, 'Добавление услуг возможно только для неоплаченных бронирований')
        return redirect('my_bookings')

    # Проверяем, есть ли уже оплата
    if hasattr(booking, 'payment_rel'):
        messages.warning(request, 'Невозможно добавить услуги к оплаченному бронированию')
        return redirect('my_bookings')

    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        quantity = request.POST.get('quantity', 1)

        if not service_id:
            messages.error(request, 'Выберите услугу')
            return redirect('add_booking_service', booking_id=booking_id)

        try:
            quantity = int(quantity)
            if quantity < 1:
                quantity = 1
            if quantity > 10:
                quantity = 10
        except ValueError:
            quantity = 1

        service = get_object_or_404(Service, pk=service_id, is_active=True)

        # Проверяем, не добавлена ли уже услуга
        booking_service, created = BookingService.objects.get_or_create(
            booking=booking,
            service=service,
            defaults={'quantity': quantity, 'price_at_time': service.price}
        )

        if not created:
            booking_service.quantity += quantity
            booking_service.save()

        # Обновляем общую стоимость бронирования
        from django.db.models import Sum, F

        # Получаем сумму всех услуг
        services_total = BookingService.objects.filter(booking=booking).aggregate(
            total=Sum(F('quantity') * F('price_at_time'))
        )['total'] or 0

        # Рассчитываем стоимость номера
        nights = (booking.check_out - booking.check_in).days
        if nights <= 0:
            nights = 1
        room_cost = nights * booking.room.price_per_night

        # Обновляем общую стоимость
        booking.total_price = room_cost + services_total
        booking.save()

        messages.success(request, f'Услуга "{service.name}" добавлена к бронированию!')
        return redirect('add_booking_service', booking_id=booking_id)  # Перенаправляем обратно на страницу услуг

    # Для GET запроса
    services = Service.objects.filter(is_active=True)

    # Рассчитываем количество ночей
    nights = (booking.check_out - booking.check_in).days
    if nights <= 0:
        nights = 1

    # Рассчитываем стоимость номера
    room_total = nights * booking.room.price_per_night

    # Рассчитываем сумму всех услуг
    from django.db.models import Sum, F
    services_total = BookingService.objects.filter(booking=booking).aggregate(
        total=Sum(F('quantity') * F('price_at_time'))
    )['total'] or 0

    return render(request, 'hotel_booking/add_service.html', {
        'booking': booking,
        'services': services,
        'nights': nights,
        'room_total': room_total,
        'services_total': services_total,
    })

# ============ Dashboard для менеджера ============
@role_required(['manager', 'admin'])
def dashboard_view(request):
    from django.db.models import Count, Sum, Q

    # Базовая статистика
    total_hotels = Hotel.objects.count()
    total_rooms = Room.objects.count()
    total_bookings = Booking.objects.count()
    total_users = User.objects.count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0

    # Бронирования по статусам
    pending_bookings = Booking.objects.filter(status='pending').count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    completed_bookings = Booking.objects.filter(status='completed').count()

    # Популярные отели - исправленный запрос без проблемного фильтра
    popular_hotels = []
    hotels = Hotel.objects.all()
    for hotel in hotels:
        booking_count = Booking.objects.filter(room__hotel=hotel).count()
        revenue = Payment.objects.filter(
            booking__room__hotel=hotel,
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        popular_hotels.append({
            'id': hotel.id,
            'name': hotel.name,
            'city': hotel.city,
            'booking_count': booking_count,
            'revenue': revenue
        })

    # Сортируем по количеству бронирований
    popular_hotels.sort(key=lambda x: x['booking_count'], reverse=True)
    popular_hotels = popular_hotels[:5]

    # Последние бронирования
    recent_bookings = Booking.objects.select_related('user', 'room__hotel').order_by('-created_at')[:10]

    context = {
        'total_hotels': total_hotels,
        'total_rooms': total_rooms,
        'total_bookings': total_bookings,
        'total_users': total_users,
        'total_revenue': total_revenue,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'completed_bookings': completed_bookings,
        'popular_hotels': popular_hotels,
        'recent_bookings': recent_bookings,
    }

    return render(request, 'hotel_booking/manage/dashboard.html', context)

# ============ Профиль пользователя ============
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'hotel_booking/profile.html', {'form': form})


# ============ Поиск и фильтрация отелей ============
def advanced_search_view(request):
    hotels = Hotel.objects.all()

    # Фильтры
    city = request.GET.get('city')
    stars = request.GET.get('stars')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    guests = request.GET.get('guests')

    if city:
        hotels = hotels.filter(city__icontains=city)
    if stars:
        hotels = hotels.filter(stars=stars)

    if min_price and max_price and check_in and check_out:
        # Фильтруем отели, у которых есть свободные номера в указанном диапазоне цен
        available_hotels = []
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

        for hotel in hotels:
            available_rooms = hotel.rooms.filter(
                is_available=True,
                price_per_night__gte=min_price,
                price_per_night__lte=max_price,
                capacity__gte=int(guests) if guests else 1
            )

            # Проверяем, свободны ли номера в выбранные даты
            for room in available_rooms:
                overlapping_bookings = room.bookings.filter(
                    status__in=['confirmed', 'pending'],
                    check_in__lt=check_out_date,
                    check_out__gt=check_in_date
                )
                if not overlapping_bookings.exists():
                    available_hotels.append(hotel.id)
                    break

        hotels = hotels.filter(id__in=available_hotels)

    return render(request, 'hotel_booking/advanced_search.html', {'hotels': hotels})
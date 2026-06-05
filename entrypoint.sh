#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Установка дополнительных пакетов если нужно
echo "Installing any missing packages..."
pip install --no-cache-dir django-filter==24.2 || true

# Применение миграций
echo "Applying database migrations..."
python manage.py makemigrations hotel_booking --noinput || true
python manage.py makemigrations api --noinput || true
python manage.py migrate --noinput

# Сбор статических файлов
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Создание суперпользователя, если его нет
echo "Creating superuser if not exists..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME:-admin}').exists():
    User.objects.create_superuser(
        username='${DJANGO_SUPERUSER_USERNAME:-admin}',
        email='${DJANGO_SUPERUSER_EMAIL:-admin@example.com}',
        password='${DJANGO_SUPERUSER_PASSWORD:-admin12345}',
        role='admin'
    )
    print("Superuser created successfully")
else:
    print("Superuser already exists")
EOF

# Создание демо-пользователей
echo "Creating demo users..."
python manage.py shell << EOF
from hotel_booking.models import User

# Создание обычного пользователя
if not User.objects.filter(username='user').exists():
    User.objects.create_user(
        username='user',
        email='user@example.com',
        password='user12345',
        first_name='Иван',
        last_name='Петров',
        phone='+7 (999) 123-45-67',
        role='user'
    )
    print("Demo user created")

# Создание менеджера
if not User.objects.filter(username='manager').exists():
    User.objects.create_user(
        username='manager',
        email='manager@example.com',
        password='manager12345',
        first_name='Анна',
        last_name='Сидорова',
        phone='+7 (999) 234-56-78',
        role='manager'
    )
    print("Demo manager created")
EOF

# Создание отелей и номеров
echo "Creating hotels and rooms..."
python manage.py seed_data

# Запуск Gunicorn
echo "Starting Gunicorn..."
exec gunicorn django_project.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2 --reload
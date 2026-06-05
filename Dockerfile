# Dockerfile
FROM python:3.11-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE django_project.settings

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements.txt
COPY requirements.txt /app/

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта
COPY . /app/

# Копирование entrypoint скрипта
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Создание директорий для статических и медиа файлов
RUN mkdir -p /app/staticfiles /app/media

# Запуск entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
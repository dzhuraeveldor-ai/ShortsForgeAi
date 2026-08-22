# ShortsForge AI — Автоматический генератор YouTube Shorts

Полноценная система для автоматического создания видео для YouTube Shorts:
- Генерация сценария и текста
- Генерация изображений
- Генерация голоса
- Автоматическое создание субтитров
- Подбор музыки и звуковых эффектов
- Автоматический монтаж видео через FFmpeg
- YouTube SEO генерация

## Установка и запуск

### 0. Получи токен бота
Напиши @BotFather в Telegram, создай нового бота и получи токен.

### Вариант 1: На компьютере (рекомендуется)
```bash
# 1. Установи FFmpeg
# Ubuntu: sudo apt install ffmpeg
# macOS: brew install ffmpeg
# Windows: скачай с ffmpeg.org

# 2. Создай .env файл
cp .env.example .env
# Открой .env и вставь:
# BOT_TOKEN=твой_токен_от_BotFather
# ADMIN_ID=8941864145

# 3. Установи зависимости
pip install -r requirements.txt

# 4. Запусти AI Worker (в отдельном терминале)
python -m worker.main

# 5. Запусти Telegram-бот (в отдельном терминале)
python -m bot.main
```

### Вариант 2: Через Docker
```bash
cp .env.example .env
# Добавь BOT_TOKEN в .env
docker-compose up -d --build
```

### Проверка работы
- Worker: открой `http://localhost:8000/health`
- Бот: напиши `/start` в Telegram своему боту

## Запуск на Render.com (бесплатный хостинг)
1. Загрузи проект на GitHub
2. Render → New Web Service → подключи репозиторий
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python -m worker.main`
5. В Environment Variables добавь:
   - `BOT_TOKEN` = твой токен
   - `ADMIN_ID` = 8941864145
   - `WORKER_API_URL` = URL твоего сервиса на Render

## Структура API
- `GET /health` — статус и возможности
- `POST /jobs` — создать задачу
- `GET /jobs/{id}` — статус задачи
- `POST /jobs/{id}/cancel` — отменить
- `POST /jobs/{id}/retry` — повторить
- `GET /models` — доступные модели
- `GET /capabilities` — возможности системы

## Структура проекта
```
ShortsForge_AI/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── database/          # База данных и модели
├── worker/            # AI Worker
│   ├── api/           # FastAPI сервер
│   ├── jobs/          # Обработка задач
│   ├── services/      # Сервисы генерации
│   ├── models/        # Управление AI моделями
│   └── utils/         # Утилиты (FFmpeg, hardware)
├── temp/              # Временные файлы
├── storage/           # Готовые видео
├── logs/              # Логи
└── models/            # Кэш AI моделей
```

## Лицензия
MIT License

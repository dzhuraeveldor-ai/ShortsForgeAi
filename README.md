# 🎬 AI SHORTS STUDIO

> **Telegram-бот для автоматического создания вертикальных видео для YouTube Shorts с помощью AI**

Полностью бесплатная, open-source система, которая превращает простой выбор параметров в готовый YouTube Short MP4 с озвучкой, субтитрами, музыкой и монтажом.

---

## ✨ Основные возможности

### 🤖 Полная автоматизация
Пользователь выбирает только основные параметры через кнопки. AI делает всё остальное:
- ✅ Придумывает идею и **Hook** (первые 3 секунды)
- ✅ Пишет полный **сценарий** (HOOK → INTRO → MAIN → PAYOFF → CTA)
- ✅ Разбивает на **сцены** с visual prompts
- ✅ Создаёт **изображения** или **видео** для каждой сцены
- ✅ Генерирует **озвучку** (TTS)
- ✅ Создаёт **субтитры** (Whisper)
- ✅ **Автоматически подбирает музыку** под нишу и настроение
- ✅ Выполняет **аудио дакинг** (музыка тише во время речи)
- ✅ Делает **автоматический монтаж** с переходами и движением камеры
- ✅ Создаёт **YouTube SEO**: 5 Titles, Description, Hashtags

### 🎯 Пользовательский опыт
- **Никаких платежей** — полностью бесплатная версия
- **Никакой ручной настройки музыки** — AI выбирает сам
- **Никакого ручного монтажа** — всё автоматически
- **Управление с телефона** через Telegram
- **Прогресс в одном сообщении** — без спама

### 🏗 Архитектура

```
┌─────────────────────────────────────────────────┐
│              Telegram Bot Server                │
│  • aiogram 3.x (async)                          │
│  • Меню, пользователи, лимиты, проекты         │
│  • Очередь задач, админ-панель                  │
│  • SQLite база данных                           │
└──────────────────────┬──────────────────────────┘
                       │ HTTP API
                       ▼
┌─────────────────────────────────────────────────┐
│                AI Worker (FastAPI)              │
│  • TEXT: Ollama (Qwen, Llama, Mistral)          │
│  • IMAGE: Stable Diffusion XL / Diffusers       │
│  • VIDEO: Wan 2.1 / LTX-Video / CogVideoX       │
│  • VOICE: Piper TTS / Kokoro                    │
│  • STT: Whisper                                 │
│  • MUSIC: Процедурная генерация / библиотека   │
│  • EDITING: FFmpeg                              │
└─────────────────────────────────────────────────┘
```

**Отказоустойчивость**: Если Worker отключён — бот продолжает работать, задачи сохраняются со статусом `WAITING_FOR_WORKER` и автоматически выполняются после подключения.

---

## 📋 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Архитектура](#архитектура)
3. [Установка и настройка](#установка-и-настройка)
4. [Запуск Bot Server](#запуск-bot-server)
5. [Запуск AI Worker](#запуск-ai-worker)
6. [Настройка AI-моделей](#настройка-ai-моделей)
7. [Telegram Setup](#telegram-setup)
8. [Админ-панель](#админ-панель)
9. [Бесплатные лимиты](#бесплатные-лимиты)
10. [Docker](#docker)
11. [Бесплатный GPU](#бесплатный-gpu)
12. [Структура проекта](#структура-проекта)
13. [API Worker](#api-worker)
14. [Устранение неполадок](#устранение-неполадок)
15. [Лицензия](#лицензия)

---

## 🚀 Быстрый старт

### 1. Клонируйте проект
```bash
git clone <your-repo-url>
cd ai_shorts_studio
```

### 2. Настройте окружение
```bash
cp .env.example .env
# Отредактируйте .env:
# - BOT_TOKEN= ваш токен от @BotFather
# - ADMIN_ID= ваш Telegram ID
# - WORKER_API_KEY= случайная строка
```

### 3. Установите зависимости
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 4. Установите FFmpeg
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg espeak

# macOS
brew install ffmpeg espeak

# Windows
# Скачайте с https://ffmpeg.org и добавьте в PATH
```

### 5. Запустите Bot Server
```bash
python bot/main.py
```

### 6. Запустите AI Worker (в отдельном терминале)
```bash
python worker/main.py
```

### 7. Проверьте
- Откройте Telegram, найдите вашего бота
- Отправьте `/start`
- Выберите **🎬 Создать Short**
- Следуйте инструкциям!

---

## 🏗 Архитектура

### Bot Server (`bot/`)
- **Telegram интерфейс**: aiogram 3.x с FSM
- **База данных**: SQLite + SQLAlchemy 2.x (async)
- **Пользователи**: регистрация, блокировка, лимиты
- **Проекты**: сохранение, статусы, история
- **Очередь**: управление задачами для Worker
- **Админ-панель**: статистика, управление пользователями
- **Middleware**: база данных, пользователи, логирование

### AI Worker (`worker/`)
- **FastAPI сервер** с защищёнными эндпоинтами (API Key)
- **Model Manager**: автоматическое определение доступных моделей
- **Text Service**: Ollama для hooks, ideas, scripts, scenes, SEO
- **Image Service**: Diffusers (Stable Diffusion XL)
- **Video Service**: интерфейсы для Wan/LTX/CogVideoX + Ken Burns fallback
- **Voice Service**: Piper TTS / Kokoro / eSpeak
- **STT Service**: Whisper для субтитров
- **Music Service**: процедурная генерация + библиотека royalty-free треков
- **Editor Service**: автоматический монтаж через FFmpeg

---

## ⚙️ Установка и настройка

### Переменные окружения (.env)

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `BOT_TOKEN` | Токен Telegram бота от @BotFather | **обязательно** |
| `ADMIN_ID` | Numeric Telegram ID администратора | 0 |
| `DATABASE_URL` | URL базы данных | `sqlite+aiosqlite:///bot.db` |
| `WORKER_URL` | URL AI Worker API | `http://localhost:8000` |
| `WORKER_API_KEY` | Ключ для доступа к Worker API | `default-worker-key` |
| `LOW_RESOURCE_MODE` | Режим ограниченных ресурсов | `true` |
| `MAX_CONCURRENT_JOBS` | Макс. параллельных задач | 1 |
| `OLLAMA_BASE_URL` | URL Ollama API | `http://localhost:11434` |
| `OLLAMA_MODEL` | Модель для текста | `qwen2:7b` |
| `WHISPER_MODEL` | Модель Whisper | `base` |
| `PIPER_VOICE` | Голос Piper TTS | `en_US-amy-medium` |

### Получение Telegram Bot Token
1. Откройте Telegram, найдите **@BotFather**
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен в `.env` → `BOT_TOKEN`

### Получение ADMIN_ID
1. Откройте Telegram, найдите **@userinfobot**
2. Отправьте любое сообщение
3. Скопируйте ваш `Id` в `.env` → `ADMIN_ID`

---

## 🤖 Запуск Bot Server

### Локально
```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Запустите бота
python bot/main.py
```

### Команды бота
| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/help` | Помощь |
| `/health` | Статус систем (Bot + Worker) |
| `/w1ndeyz` | Админ-панель (только ADMIN_ID) |

### Проверка работоспособности
1. Отправьте `/start` — должно появиться главное меню
2. Отправьте `/health` — проверьте статус Bot и Worker
3. Отправьте `/w1ndeyz` (админам) — должна открыться админ-панель

---

## ⚙️ Запуск AI Worker

### Локально
```bash
# В отдельном терминале
source venv/bin/activate
python worker/main.py
```

Worker запустится на `http://localhost:8000`

### Проверка Worker
```bash
# Проверка health
curl http://localhost:8000/health

# Документация API
http://localhost:8000/docs
```

### Запуск только Bot Server (без Worker)
Bot Server работает автономно. Если Worker отключён:
- Пользователь может пройти все шаги настроек
- Задачи сохраняются в базе со статусом `WAITING_FOR_WORKER`
- После запуска Worker задачи могут быть обработаны

---

## 🧠 Настройка AI-моделей

### 1. Ollama (генерация текста)
```bash
# Установка Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Загрузка модели (рекомендуется)
ollama pull qwen2:7b

# Альтернативы:
ollama pull llama3:8b
ollama pull mistral:7b
ollama pull gemma:7b
```

Проверка: `curl http://localhost:11434/api/tags`

### 2. Stable Diffusion (изображения)
```bash
# Установите дополнительные зависимости
pip install diffusers transformers accelerate torch safetensors

# Модели загружаются автоматически при первом запуске
# SDXL: ~10 GB диска, рекомендуется GPU с 8GB+ VRAM
```

Без GPU работает на CPU, но очень медленно.

### 3. Piper TTS (озвучка)
```bash
pip install piper-tts

# Голосовые модели загружаются автоматически
# или укажите PIPER_MODEL_PATH в .env
```

### 4. Whisper (субтитры)
```bash
pip install openai-whisper

# Также требуется ffmpeg (уже установлен)
# Модели: tiny, base, small, medium, large
# По умолчанию: base (~145 MB, хороший баланс)
```

### 5. Видео-модели (опционально)
Видео-модели требуют значительных ресурсов (GPU 16GB+ VRAM):

- **Wan 2.1**: `Wan-AI/Wan2.1-T2V-14B`
- **LTX-Video**: `Lightricks/LTX-Video`
- **CogVideoX**: `THUDM/CogVideoX-5b`

Установка:
```bash
# Пример для Wan 2.1
pip install diffusers accelerate transformers sentencepiece
```

**Без полноценной видео-модели** система использует **Ken Burns эффект** на сгенерированных изображениях — стабильно и быстро работает на любом оборудовании.

---

## 👑 Админ-панель

Доступна по команде `/w1ndeyz` только пользователю с `ADMIN_ID`.

### Возможности
- 📊 **Статистика**: пользователи, проекты, задачи (Today / 7d / 30d / All)
- 👥 **Пользователи**: список последних зарегистрировавшихся
- 🔎 **Поиск пользователя** по ID
- 🚫 **Блокировка / разблокировка**
- 🎁 **Выдача дополнительных лимитов**
- 🔄 **Сброс лимитов**
- ♾️ **Назначение Unlimited**
- 📢 **Рассылка** всем пользователям
- 🤖 **Статус AI Worker**: GPU, VRAM, доступные модели
- 🎨 **Статус моделей**
- 📋 **Очередь задач**
- 💾 **Использование хранилища**

### Преимущества админа
- **Безлимитный доступ** ко всем функциям
- Лимиты не применяются
- Доступ ко всем админ-командам

---

## 📊 Бесплатные лимиты

Используется **скользящее 24-часовое окно**.

| Функция | Лимит на 24ч |
|---------|-------------|
| 💡 Ideas | 10 |
| ✍️ Scripts | 5 |
| 🪝 Hooks | 10 |
| 🖼 Images | 5 |
| 🎥 AI Videos | 1 |
| 🎙 Voice | 3 |
| 📝 Subtitles | 3 |
| 🎬 Full Shorts | 1 |
| 🔍 Analysis | 3 |

Админ (`ADMIN_ID`) получает **♾️ Unlimited** автоматически.

---

## 🐳 Docker

### Запуск всего стека
```bash
# Сборка и запуск
docker compose up --build

# Только Bot Server
docker compose up bot

# Только AI Worker
docker compose up worker

# Фоновый режим
docker compose up -d

# Остановка
docker compose down
```

### GPU поддержка в Docker
Для использования GPU в контейнере установите **NVIDIA Container Toolkit**:
```bash
# Ubuntu
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Затем раскомментируйте секцию `deploy.resources` в `docker-compose.yml`.

---

## ☁️ Бесплатный GPU

### Google Colab (Kaggle)
Можно запустить AI Worker в Google Colab с бесплатным GPU T4:

```python
# В ячейке Colab:
!git clone <your-repo>
%cd ai_shorts_studio
!pip install -r requirements.txt
!pip install diffusers transformers accelerate torch piper-tts openai-whisper
!apt-get install ffmpeg espeak -y

# Установите переменные окружения
import os
os.environ['WORKER_API_KEY'] = 'your-key'

# Запустите Worker в фоне
!nohup python worker/main.py &

# Используйте ngrok для доступа извне
!pip install pyngrok
from pyngrok import ngrok
ngrok.connect(8000)
# Полученный URL укажите в WORKER_URL на Bot Server
```

### Важные ограничения бесплатных GPU
- ⏱ **Ограничение по времени**: сессии обычно 12 часов
- 🔄 **Сброс при отключении**: все данные теряются
- 📊 **Ограничение использования**: при интенсивном использовании GPU могут временно отключить
- 🚀 **Не гарантировано**: бесплатный GPU может быть недоступен в пиковые часы

**Рекомендация**: Используйте бесплатный GPU для тестирования. Для стабильной работы рассмотрите выделенные GPU-инстансы.

---

## 📁 Структура проекта

```
ai_shorts_studio/
├── bot/                          # Telegram Bot Server
│   ├── main.py                   # Точка входа бота
│   ├── config.py                 # Конфигурация бота
│   ├── handlers/                 # Обработчики сообщений и кнопок
│   │   ├── middleware.py         # Middleware (БД, пользователи, логи)
│   │   ├── commands.py           # /start, /help, /w1ndeyz, /health
│   │   ├── workflow.py           # Workflow создания Short (9 шагов)
│   │   ├── projects.py           # Управление проектами
│   │   └── admin.py              # Админ-панель
│   ├── keyboards/                # Все inline-клавиатуры
│   │   └── __init__.py
│   ├── services/                 # Бизнес-логика
│   │   ├── worker_client.py      # HTTP-клиент к AI Worker
│   │   ├── workflow.py           # Менеджер состояния workflow
│   │   └── generation.py         # Пайплайн генерации с прогрессом
│   └── utils/                    # Вспомогательные функции
│       └── __init__.py
│
├── database/                     # Слой базы данных
│   ├── database.py               # Подключение и сессии
│   ├── models.py                 # ORM модели (SQLAlchemy)
│   └── repositories.py           # Data Access Layer
│
├── worker/                       # AI Worker (FastAPI)
│   ├── main.py                   # Точка входа Worker
│   ├── config.py                 # Конфигурация Worker
│   ├── api/                      # API роуты
│   │   └── routes.py             # Все эндпоинты
│   ├── models/                   # Pydantic схемы
│   │   └── __init__.py
│   ├── services/                 # AI сервисы
│   │   ├── model_manager.py      # Детектор доступных моделей
│   │   ├── text/                 # Ollama (hooks, ideas, script, scenes, SEO)
│   │   ├── image/                # Diffusers (Stable Diffusion)
│   │   ├── video/                # Wan/LTX/CogVideoX + Ken Burns
│   │   ├── voice/                # Piper / Kokoro / eSpeak
│   │   ├── stt/                  # Whisper (субтитры)
│   │   ├── music/                # Процедурная музыка + библиотека
│   │   └── editor/               # FFmpeg монтаж
│   └── utils/
│       └── __init__.py
│
├── storage/                      # Постоянное хранилище
├── temp/                         # Временные файлы (автоочистка)
├── logs/                         # Логи
├── requirements.txt              # Python зависимости
├── Dockerfile                    # Docker образ
├── docker-compose.yml            # Docker Compose
├── .env.example                  # Пример конфигурации
├── .gitignore
└── README.md                     # Этот файл
```

---

## 🔌 API Worker

### Аутентификация
Все запросы (кроме `/health` и `/`) требуют заголовок:
```
X-API-Key: your_worker_api_key
```

### Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/health` | Статус Worker, GPU, модели |
| `POST` | `/jobs` | Создать задачу |
| `GET` | `/jobs/{id}` | Статус и результат задачи |
| `POST` | `/jobs/{id}/cancel` | Отменить задачу |
| `POST` | `/generate/text` | Генерация текста |
| `POST` | `/generate/hooks` | Генерация Hooks |
| `POST` | `/generate/ideas` | Генерация идей |
| `POST` | `/generate/script` | Генерация сценария |
| `POST` | `/generate/scenes` | Разбивка на сцены |
| `POST` | `/generate/image` | Генерация изображения |
| `POST` | `/generate/voice` | Генерация озвучки |
| `POST` | `/generate/subtitles` | Генерация субтитров |
| `POST` | `/generate/seo` | YouTube SEO метаданные |
| `POST` | `/render` | Полный рендер видео |

Интерактивная документация: `http://localhost:8000/docs`

---

## 🎵 Добавление своей музыки

Поместите royalty-free/CC0 треки в директорию:
```
storage/music/<style>/track.mp3
```

Где `<style>` — один из: `horror`, `motivation`, `luxury`, `facts`, `funny`, `science`, `history`, `gaming`, `animals`, `mystery`, `ai`, `storytelling`, `money`, `space`, `technology`, `education`, `sports`.

Поддерживаемые форматы: MP3, WAV, OGG, FLAC.

---

## 🔧 Устранение неполадок

### Проблема: Бот не отвечает
- Проверьте `BOT_TOKEN` в `.env`
- Проверьте логи: `logs/bot_YYYY-MM-DD.log`
- Убедитесь, что бот не заблокирован в Telegram

### Проблема: Worker показывает Offline
- Проверьте, запущен ли Worker: `python worker/main.py`
- Проверьте `WORKER_URL` и `WORKER_API_KEY` совпадают на боте и воркере
- Проверьте порт 8000 не занят другим процессом

### Проблема: Ollama не найден
- Установите Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
- Запустите сервис: `ollama serve`
- Загрузите модель: `ollama pull qwen2:7b`

### Проблема: FFmpeg ошибки
- Убедитесь, что FFmpeg установлен: `ffmpeg -version`
- Для Ubuntu: `sudo apt-get install ffmpeg`

### Проблема: Очень медленная генерация
- Без GPU генерация изображений и видео работает очень медленно
- Включите `LOW_RESOURCE_MODE=true`
- Используйте меньшие модели Whisper (`tiny` вместо `base`)

### Проблема: База данных заблокирована
- Убедитесь, что только один экземпляр бота запущен
- SQLite не поддерживает высокую параллельность — для продакшена используйте PostgreSQL

### Проблема: Ошибка импорта модулей
- Убедитесь, что вы запускаете из корня проекта
- Проверьте, что виртуальное окружение активировано
- Переустановите зависимости: `pip install -r requirements.txt`

---

## 🛡 Безопасность

- ✅ SQL Injection защита через SQLAlchemy ORM
- ✅ Валидация всех пользовательских входных данных
- ✅ API Key аутентификация Worker
- ✅ Нет выполнения shell команд из пользовательского ввода
- ✅ Ограничение размера файлов
- ✅ Rate limiting через лимиты пользователей
- ✅ Логирование всех действий (без чувствительных данных)

---

## 📝 Примечания

- **Никаких платежей**: проект полностью бесплатный, без Telegram Stars, крипты и карт
- **Никаких фейковых функций**: если модель недоступна — показывается честное сообщение
- **Отказоустойчивость**: Worker может отключаться и подключаться без потери данных
- **Масштабируемость**: архитектура позволяет добавлять больше Worker
- **Телефон-first**: весь интерфейс оптимизирован для мобильного Telegram

---

## 🔮 Планы на будущее

- [ ] Поддержка PostgreSQL вместо SQLite для продакшена
- [ ] Redis для очереди задач
- [ ] Интеграция с дополнительными видео-моделями
- [ ] Веб-интерфейс для админа
- [ ] Экспорт проектов в JSON
- [ ] Пакетная генерация
- [ ] Пользовательские библиотеки музыки и SFX
- [ ] Поддержка нескольких языков интерфейса бота

---

## 📄 Лицензия

MIT License — свободное использование, модификация и распространение.

---

## 🙏 Благодарности

- **Ollama** — локальный запуск LLM
- **Stable Diffusion / Diffusers** — генерация изображений
- **Piper TTS** — быстрая качественная озвучка
- **Whisper** — точное распознавание речи
- **FFmpeg** — стандарт видео-индустрии
- **aiogram** — лучший фреймворк для Telegram ботов
- **FastAPI** — современный веб-фреймворк для API

---

**Создано с ❤️ для создателей контента**

Превратите идею в готовый YouTube Short за минуты!

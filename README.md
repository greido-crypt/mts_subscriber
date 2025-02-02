# 📱 mts_subscriber

## 📌 Описание проекта
**mts_subscriber** — это Telegram-бот, который помогает пользователям **получить подписку МТС Премиум** за **2₽ вместо 300₽** в месяц, используя механизм "семейной подписки".  
Для автоматизации регистрации используется **Selenium** и **SMS-Activate API**.

---

## 🚀 Функциональность
- 📲 **Авторизация через SMS-код**: Пользователь вводит номер телефона, получает SMS и входит в бота.
- 🔑 **Регистрация нового аккаунта**: Бот создает аккаунт на одноразовый номер через **SMS-Activate API**.
- 🏷 **Активация подписки**: Оформляется **тестовая подписка на 3 месяца**.
- 🔄 **Получение secure-данных**: Через **Selenium** бот заходит на страницу авторизации **МТС**, берет временные **secure данные** и использует их в **cookies API-запросов**.
- 📩 **Приглашение в семью**: Бот добавляет пользователя в семейную подписку, что позволяет **экономить**.
- 🤖 **Telegram-бот**: Взаимодействие через удобный интерфейс.

---

## 📂 Структура проекта
```plaintext
mts_subscriber/
│── api/                   # API сервисы
│   ├── default/           # Базовые API-запросы
│   ├── ipify/             # Работа с IP
│   ├── mts/               # Запросы к API МТС
│   ├── sms_activate/      # Покупка номеров через SMS-Activate
│── db/                    # База данных
│   ├── models/            # SQLAlchemy модели
│── repository/            # Взаимодействие с БД
│── telegram_bot/          # Telegram-бот на Aiogram
│   ├── handlers/          # Обработчики команд
│   ├── utils/             # Утилиты для работы бота
│── selenium/              # Selenium скрипты для автоматизации
│── .env                   # Файл конфигурации
│── requirements.txt       # Список зависимостей
│── README.md              # Описание проекта
```

---

## 🔧 Установка и запуск

### 1️⃣ Клонирование репозитория
```sh
git clone https://github.com/greido-crypt/mts_subscriber.git
cd mts_subscriber
```

### 2️⃣ Настройка окружения
```sh
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows
```

### 3️⃣ Установка зависимостей
```sh
pip install -r requirements.txt
```

### 4️⃣ Запуск Selenium для получения secure-данных
```sh
python selenium/auth_mts.py
```

### 5️⃣ Запуск FastAPI сервера
```sh
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6️⃣ Запуск Telegram-бота
```sh
python telegram_bot/utils/app.py
```

---

## 🛠 Используемые технологии
- **FastAPI** — серверная часть API
- **Aiogram** — Telegram-бот
- **SQLAlchemy + asyncpg** — база данных PostgreSQL
- **SMS-Activate API** — покупка одноразовых номеров для регистрации
- **Selenium** — автоматизация входа в аккаунт МТС и получение secure-данных
- **Uvicorn** — ASGI сервер
- **dotenv** — хранение конфигурации

---

## 🤝 Контрибьютинг
Хотите помочь проекту```

1. **Форкните** репозиторий.
2. **Создайте новую ветку** (```sh git checkout -b feature-branch ```).
3. **Добавьте изменения** и закоммитьте (```sh git commit -m "Добавлена новая фича" ```).
4. **Запушьте** ветку (```sh git push origin feature-branch ```).
5. **Создайте Pull Request**.

---

## 📜 Лицензия
Этот проект распространяется под **MIT License**.

---

## 📞 Контакты
Если у вас есть вопросы или предложения, свяжитесь со мной через GitHub.

🚀 **Развивайте проект и экономьте на подписке!** 😊

1. Архітектура проєкту
Система складається з чотирьох основних вузлів: бази даних, брокера повідомлень та двох незалежних мікросервісів, які не знають про існування один одного напряму, а спілкуються виключно через чергу.

База даних (Supabase PostgreSQL): Зберігає таблиці affiliates, offers, leads. Обидва сервіси мають доступ до БД (наприклад, landings має читати таблицю affiliates для валідації токена, а core — писати ліди та читати агреговані дані).

Брокер повідомлень (Upstash Redis): * Черга (leads_queue): landings публікує сюди валідовані ліди (наприклад, через RPUSH).

Кеш дедуплікації: core використовує Redis для зберігання ключів (хешів лідів) з TTL 10 хвилин.

Сервіс 1: Landings (/landings): Приймає POST-запити, валідує JWT, перевіряє наявність affiliate_id у БД, валідує тіло запиту. Якщо все ок — пакує дані в JSON і відправляє у Redis-чергу. Повертає 200 OK.

Сервіс 2: Core (/core): * API-частина: Обробляє GET-запити для видачі аналітики з БД (з перевіркою JWT).

Фоновий воркер: Асинхронний процес (наприклад, за допомогою asyncio.create_task при старті FastAPI або окремим процесом), який постійно слухає Redis (через BLPOP), дістає ліди, перевіряє на дублікати через Redis, і якщо дублікату немає — записує в PostgreSQL.

2. Структура проєкту (Monorepo)
Для зручності підтримки двох сервісів в одному репозиторії, краще винести спільну логіку (моделі БД, підключення, утиліти для JWT) в окрему папку common.

Plaintext
project_root/
├── alembic/                # Файли міграцій БД
├── alembic.ini             # Конфіг Alembic
├── common/                 # Спільний код для обох сервісів
│   ├── __init__.py
│   ├── database.py         # Налаштування SQLAlchemy (async engine)
│   ├── models.py           # Декларативні моделі (Lead, Offer, Affiliate)
│   ├── schemas.py          # Базові Pydantic схеми
│   └── security.py         # Логіка декодування/валідації JWT
├── landings/               # Мікросервіс прийому лідів
│   ├── __init__.py
│   ├── main.py             # FastAPI app для Landings
│   ├── router.py           # Ендпоінт POST /lead
│   └── redis_client.py     # Клієнт для відправки в чергу
├── core/                   # Мікросервіс обробки та аналітики
│   ├── __init__.py
│   ├── main.py             # FastAPI app для Core
│   ├── router.py           # Ендпоінти GET /leads
│   ├── worker.py           # Фоновий процес читання з Redis
│   └── deduplication.py    # Логіка перевірки дублікатів (Redis TTL)
├── Dockerfile.landings     # Докерфайл для 1-го сервісу
├── Dockerfile.core         # Докерфайл для 2-го сервісу
├── requirements.txt        # Спільні залежності (fastapi, asyncpg, redis, etc.)
└── README.md               # Інструкції
3. План дій (Roadmap)
Етап 1: Підготовка інфраструктури (Безкоштовно)

Зареєструватися в Supabase, створити проєкт. Отримати DATABASE_URL (з Transaction Pooler, порт 6543).

Зареєструватися в Upstash, створити базу Redis. Отримати REDIS_URL.

Етап 2: База та спільний код

Створити віртуальне середовище, встановити залежності.

Описати models.py (таблиці affiliates, offers, leads з полем created_at).

Налаштувати Alembic, згенерувати та застосувати першу міграцію (alembic upgrade head).

Написати security.py (функцію verify_token(token: str, db: AsyncSession)).

Етап 3: Сервіс Landings

Реалізувати Pydantic схему для вхідного ліда.

Написати ендпоінт POST /lead у landings/router.py.

Додати Dependency для перевірки Bearer токена.

Додати публікацію JSON-рядка ліда в leads_queue (Redis).

Етап 4: Сервіс Core

Написати логіку worker.py: нескінченний цикл while True, який робить blpop("leads_queue").

Реалізувати дедуплікацію: генерація хешу з name+phone+offer_id+affiliate_id. Перевірка через Redis SETNX (або GET + SET з EX=600).

Запис ліда в PostgreSQL.

Написати ендпоінт GET /leads з агрегацією SQLAlchemy (func.count, group_by).

Підключити запуск воркера на подію старту FastAPI (lifespan event).

Етап 5: Контейнеризація та Документація

Написати два Dockerfile.

Заповнити README.md (інструкції для локального запуску через uvicorn або docker-compose).

4. Інструкції для розгортання проєкту
Оскільки Hugging Face Spaces обмежує один Space одним відкритим портом, ми розгорнемо сервіси як два окремі Spaces, підключені до одного GitHub-репозиторію. Це ідеально відповідає мікросервісній архітектурі.

Крок 1. Завантаження коду
Створи репозиторій на GitHub і запуш туди весь код проєкту з готовими Dockerfile.landings та Dockerfile.core.

Приклад Dockerfile.landings:

Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# HF Spaces очікує, що сервіс слухає порт 7860
CMD ["uvicorn", "landings.main:app", "--host", "0.0.0.0", "--port", "7860"]
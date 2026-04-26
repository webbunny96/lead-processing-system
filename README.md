# Lead Processing System

Бекенд-система для прийому та обробки лідів, реалізована як 2 незалежні FastAPI мікросервіси в одному репозиторії:

- `landings` — приймає ліди (`POST /lead`), валідовує Bearer JWT, перевіряє вхідні дані, кладе лід у Redis-чергу.
- `core` — запускає фоновий воркер, читає чергу, виконує дедуплікацію (10 хв), зберігає нові ліди в PostgreSQL, віддає аналітику (`GET /leads`).

Сервіси взаємодіють між собою тільки через Redis.

## Відповідність ТЗ

- Стек: `Python`, `FastAPI`, `PostgreSQL`, `SQLAlchemy 2 + asyncpg`, `Alembic`, `Redis`, `JWT`.
- 2 мікросервіси: `landings` та `core`.
- Bearer токен перевіряється в обох сервісах, payload має формат `{"id": affiliates.id}`.
- Якщо `affiliates.id` з токена відсутній у БД — запит відхиляється (`401`).
- Реалізовані таблиці: `affiliates`, `offers`, `leads`; у `leads` зберігається `created_at`.
- Дедуплікація: `name + phone + offer_id + affiliate_id` з TTL 600 секунд у Redis.

## Структура проєкту

- `common/` — спільні модулі (БД, моделі, pydantic-схеми, JWT security).
- `landings/` — API прийому лідів + Redis producer.
- `core/` — API аналітики + фоновий worker + дедуплікація.
- `alembic/` — міграції схеми БД.
- `generate_token.py` — утиліта для генерації тестового JWT.
- `deploy.py` — синхронізація файлів у deploy-репозиторії.

## Архітектура стеку

### Компоненти

- **API-шар:** два незалежні FastAPI сервіси (`landings`, `core`).
- **Черга повідомлень:** Redis використовується як транспорт між сервісами (`RPUSH`/`BLPOP`).
- **Фонова обробка:** воркер у `core` працює у lifespan-процесі сервісу.
- **Персистентність:** PostgreSQL + SQLAlchemy 2 (async) для таблиць `affiliates`, `offers`, `leads`.
- **Схема БД:** Alembic міграції (`0001_initial_schema`, `0002_add_country_to_leads`).
- **Аутентифікація:** JWT Bearer з payload `{"id": <affiliate_id>}`, перевірка існування affiliate у БД.

### Потік даних

1. Клієнт викликає `POST /lead` у `landings` з Bearer JWT.
2. `landings` валідовує payload, токен, відповідність `affiliate_id` і доступність `offer_id`.
3. Валідний лід публікується в Redis-чергу (`LEADS_QUEUE_NAME`).
4. `core`-воркер читає чергу, виконує дедуплікацію у Redis (TTL 10 хвилин).
5. Якщо лід новий, `core` зберігає запис у PostgreSQL (`leads`).
6. `GET /leads` у `core` віддає аналітику для affiliate з токена з групуванням `date` або `offer`.

## Налаштування оточення

1. Створіть `.env`:

```bash
copy .env.example .env
```

2. Заповніть змінні:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:6543/DB_NAME
REDIS_URL=redis://default:password@host:6379
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
LEADS_QUEUE_NAME=leads_queue
```

## Локальний запуск

### 1) Встановлення залежностей

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Міграції БД

```bash
alembic upgrade head
```

### 3) Запуск сервісів (у різних терміналах)

`landings`:

```bash
uvicorn landings.main:app --reload --port 8001
```

`core`:

```bash
uvicorn core.main:app --reload --port 8002
```

## Деплой на цей стек

Нижче інструкція для деплою двох контейнеризованих сервісів FastAPI на стеку `Docker + PostgreSQL + Redis`.

### 1) Підготуйте інфраструктуру

- Підніміть PostgreSQL (керований сервіс або окремий контейнер/інстанс).
- Підніміть Redis (керований сервіс або окремий контейнер/інстанс).
- Створіть окремі точки деплою для:
  - `landings` (HTTP API),
  - `core` (HTTP API + фоновий воркер).

### 2) Створіть образи сервісів

З кореня репозиторію:

```bash
docker build -f Dockerfile.landings -t lead-landings:latest .
docker build -f Dockerfile.core -t lead-core:latest .
```

### 3) Налаштуйте змінні оточення для обох сервісів

Обов'язково однакові (окрім специфічних platform/env значень):

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `LEADS_QUEUE_NAME`

Приклад:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:6543/DB_NAME
REDIS_URL=redis://default:password@host:6379
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
LEADS_QUEUE_NAME=leads_queue
```

### 4) Застосуйте міграції перед стартом трафіку

Окремим job/release command:

```bash
alembic upgrade head
```

### 5) Запустіть контейнери сервісів

`Dockerfile.landings` запускає:

```bash
uvicorn landings.main:app --host 0.0.0.0 --port 7860
```

`Dockerfile.core` запускає:

```bash
uvicorn core.main:app --host 0.0.0.0 --port 7860
```

На платформі деплою (Render/Railway/Fly.io/HuggingFace Docker Space/VPS) прокиньте зовнішній порт на `7860` у відповідному контейнері.

### 6) Перевірка після деплою

- Відкрийте `/docs` для обох сервісів.
- Перевірте `POST /lead` валідним токеном і payload.
- Переконайтесь, що `GET /leads` повертає дані після обробки воркером.
- Перевірте дедуплікацію: повторний однаковий лід протягом 10 хв не має додаватися вдруге.

## Початкові дані для перевірки

Перед тестуванням API потрібно мати в БД:

- хоча б 1 запис у `affiliates` (наприклад, `id=1`);
- хоча б 1 запис у `offers` з правильним `affiliate_id`.

Приклад payload токена повинен містити `id` існуючого affiliate:

```json
{"id": 1}
```

Згенерувати тестовий токен:

```bash
python generate_token.py
```

## API

### `landings` — `POST /lead`

- Header: `Authorization: Bearer <jwt>`
- Body:

```json
{
  "name": "Олексій",
  "phone": "+380982342123",
  "country": "UA",
  "offer_id": 1,
  "affiliate_id": 1
}
```

Валідація:

- усі поля обов'язкові;
- `country` має бути у форматі ISO 3166-1 alpha-2 (2 великі латинські літери);
- `affiliate_id` у body має збігатися з `id` у Bearer токені;
- `offer_id` має належати цьому affiliate.

Успішний результат: `200` + `{"status":"ok"}`, лід ставиться в Redis-чергу.

### `core` — `GET /leads`

- Header: `Authorization: Bearer <jwt>`
- Query params:
  - `date_from=YYYY-MM-DD`
  - `date_to=YYYY-MM-DD`
  - `group=date|offer`

Повертає тільки дані affiliate з токена:

- `group=date` — кількість і список лідів по днях;
- `group=offer` — кількість і список лідів по офферах.

## Swagger

- `landings`: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- `core`: [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs)

## Відхилення/уточнення відносно ТЗ

- У таблиці `offers` додано поле `affiliate_id` (додатковий зв'язок оффера з афіліатом), щоб явно валідувати доступність оффера для конкретного affiliate.
- У таблиці `affiliates` є поле `token_sub` (додатковий технічний атрибут), що не конфліктує з вимогами ТЗ.

## Статус тестів

Юніт-тести у репозиторії поки не додані.

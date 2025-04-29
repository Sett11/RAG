# LinkStorage API

API для хранения и управления пользовательскими ссылками и коллекциями.

## Возможности

- Регистрация и аутентификация пользователей
- Сброс и смена пароля
- Управление ссылками (создание, просмотр, обновление, удаление)
- Управление коллекциями (создание, просмотр, обновление, удаление)
- Автоматическое извлечение метаданных ссылок

## Требования

- Docker
- Docker Compose

## Быстрый старт

1. Клонируйте репозиторий:
   ```bash
   git clone <repo_url>
   cd linkstorage
   ```
2. Соберите и запустите сервисы:
   ```bash
   docker-compose up --build
   ```
3. API будет доступен по адресу: [http://localhost:8000](http://localhost:8000)
4. Swagger-документация: [http://localhost:8000/docs](http://localhost:8000/docs)

## Работа с миграциями Alembic

- Применить миграции:
  ```bash
  docker-compose run --rm web alembic upgrade head
  ```
- Создать новую миграцию:
  ```bash
  docker-compose run --rm web alembic revision --autogenerate -m "описание"
  ```

## Тестирование

- Запуск тестов с покрытием:
  ```bash
  docker-compose run --rm web pytest --cov=app
  ```
  или локально:
  ```bash
  pytest --cov=app
  ```

## Основные эндпоинты API

- `POST /register` — регистрация пользователя
- `POST /login` — аутентификация
- `GET /users/me` — информация о текущем пользователе
- `PUT /users/me/password` — смена пароля
- `POST /password-reset` — запрос на сброс пароля
- `POST /password-reset/confirm` — подтверждение сброса пароля
- `GET /links/` — получить ссылки пользователя
- `POST /links/` — создать новую ссылку
- `PUT /links/{link_id}` — обновить ссылку
- `DELETE /links/{link_id}` — удалить ссылку
- `GET /collections/` — получить коллекции пользователя
- `POST /collections/` — создать новую коллекцию
- `PUT /collections/{collection_id}` — обновить коллекцию
- `DELETE /collections/{collection_id}` — удалить коллекцию

## Примеры запросов

### Регистрация пользователя
```http
POST /register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

### Аутентификация (получение токена)
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

### Получение информации о пользователе
```http
GET /users/me
Authorization: Bearer <access_token>
```

### Добавление новой ссылки
```http
POST /links/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "url": "https://example.com"
}
```

### Создание новой коллекции
```http
POST /collections/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Моя коллекция",
  "description": "Описание коллекции (необязательно)"
}
```

### Добавление ссылки в коллекцию
```http
POST /collections/{collection_id}/add_link/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "link_id": 1
}
```

## Структура проекта

- `app/` — исходный код приложения (роутеры, модели, схемы, бизнес-логика)
- `alembic/` — миграции базы данных
- `tests/` — тесты
- `logs/` — логи приложения
- `Dockerfile`, `docker-compose.yml` — файлы для сборки и запуска

---

**Вопросы и предложения — в Issues!**
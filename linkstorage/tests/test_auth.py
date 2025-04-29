"""
Тесты для проверки регистрации, аутентификации и работы токенов.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_and_login(tmp_path):
    """
    Проверяет регистрацию нового пользователя, вход и получение токена.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Регистрация нового пользователя
        response = await ac.post("/register", json={"email": "testuser@example.com", "password": "testpass123"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["is_active"] is True
        assert "id" in data

        # Попытка повторной регистрации (должна быть ошибка)
        response = await ac.post("/register", json={"email": "testuser@example.com", "password": "testpass123"})
        assert response.status_code in (400, 409)

        # Вход с правильными данными
        response = await ac.post("/login", data={"username": "testuser@example.com", "password": "testpass123"})
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Вход с неправильным паролем
        response = await ac.post("/login", data={"username": "testuser@example.com", "password": "wrongpass"})
        assert response.status_code == 400
        assert "Incorrect email or password" in response.text

@pytest.mark.asyncio
async def test_password_reset_flow(tmp_path):
    """
    Проверяет полный цикл сброса пароля: запрос, подтверждение, вход с новым паролем.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Регистрация пользователя
        email = "resetuser@example.com"
        old_password = "oldpass123"
        new_password = "newpass456"
        await ac.post("/register", json={"email": email, "password": old_password})

        # Запрос сброса пароля
        response = await ac.post("/reset-password/request", json={"email": email})
        assert response.status_code == 200
        data = response.json()
        assert "Токен для сброса пароля" in data["message"]
        token = data["message"].split(": ")[-1]
        assert len(token) > 10

        # Подтверждение сброса пароля с валидным токеном
        response = await ac.post("/reset-password/confirm", json={"token": token, "new_password": new_password})
        assert response.status_code == 200
        assert "Пароль успешно сброшен" in response.json()["message"]

        # Вход с новым паролем
        response = await ac.post("/login", data={"username": email, "password": new_password})
        assert response.status_code == 200
        assert "access_token" in response.json()

        # Вход со старым паролем не должен работать
        response = await ac.post("/login", data={"username": email, "password": old_password})
        assert response.status_code == 400

        # Повторное использование токена не допускается
        response = await ac.post("/reset-password/confirm", json={"token": token, "new_password": "anotherpass"})
        assert response.status_code == 400
        assert "Invalid or expired token" in response.text

@pytest.mark.asyncio
async def test_password_reset_request_nonexistent_email(tmp_path):
    """
    Проверяет, что сброс пароля для несуществующего email возвращает корректный ответ.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/reset-password/request", json={"email": "no_such_user@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert "Если email зарегистрирован" in data["message"]

@pytest.mark.asyncio
async def test_password_reset_expired_token(tmp_path):
    """
    Проверяет, что подтверждение сброса пароля с истёкшим токеном возвращает ошибку.
    """
    from app.database import SessionLocal
    from app.models.user import User
    from datetime import datetime, timedelta, UTC
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Регистрация пользователя
        email = "expiredtoken@example.com"
        password = "testpass123"
        await ac.post("/register", json={"email": email, "password": password})
        # Получаем токен сброса пароля
        response = await ac.post("/reset-password/request", json={"email": email})
        token = response.json()["message"].split(": ")[-1]
        # Принудительно делаем токен истёкшим
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            user.reset_password_token_expiration = datetime.now(UTC) - timedelta(hours=2)
            db.commit()
        # Пробуем подтвердить сброс пароля с истёкшим токеном
        response = await ac.post("/reset-password/confirm", json={"token": token, "new_password": "newpass"})
        assert response.status_code == 400
        assert "Invalid or expired token" in response.text 
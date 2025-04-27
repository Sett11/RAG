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
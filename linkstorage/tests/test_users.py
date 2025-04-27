"""
Тесты для проверки пользовательских операций: получение информации о себе и смена пароля.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_user_info_and_password_change():
    """
    Проверяет получение информации о себе и смену пароля.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Регистрация и вход
        await ac.post("/register", json={"email": "user2@example.com", "password": "pass12345"})
        login_resp = await ac.post("/login", data={"username": "user2@example.com", "password": "pass12345"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Получение информации о себе
        resp = await ac.get("/users/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user2@example.com"
        assert data["is_active"] is True
        assert "id" in data

        # Смена пароля
        resp = await ac.put("/users/me/password", params={"new_password": "newpass987"}, headers=headers)
        assert resp.status_code == 200
        assert "Password updated successfully" in resp.text

        # Вход со старым паролем (должен быть неудачным)
        resp = await ac.post("/login", data={"username": "user2@example.com", "password": "pass12345"})
        assert resp.status_code == 400

        # Вход с новым паролем (должен быть успешным)
        resp = await ac.post("/login", data={"username": "user2@example.com", "password": "newpass987"})
        assert resp.status_code == 200 
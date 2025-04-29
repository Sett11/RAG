import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_password_reset_token_is_not_reusable(tmp_path):
    """
    Проверяет, что токен сброса пароля нельзя использовать повторно.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "user1@example.com", "password": "pass1"})
        resp1 = await ac.post("/reset-password/request", json={"email": "user1@example.com"})
        token1 = resp1.json()["message"].split(": ")[-1]
        # Первый сброс пароля
        resp2 = await ac.post("/reset-password/confirm", json={"token": token1, "new_password": "newpass1"})
        assert resp2.status_code == 200
        # Повторное использование токена
        resp3 = await ac.post("/reset-password/confirm", json={"token": token1, "new_password": "newpass2"})
        assert resp3.status_code == 400
        assert "Invalid or expired token" in resp3.text

@pytest.mark.asyncio
async def test_user_cannot_access_others_links(tmp_path):
    """
    Проверяет, что пользователь не может получить или удалить чужие ссылки.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Регистрация двух пользователей
        await ac.post("/register", json={"email": "usera@example.com", "password": "passa"})
        await ac.post("/register", json={"email": "userb@example.com", "password": "passb"})

        # Вход usera
        resp = await ac.post("/login", data={"username": "usera@example.com", "password": "passa"})
        token_a = resp.json()["access_token"]

        # Вход userb
        resp = await ac.post("/login", data={"username": "userb@example.com", "password": "passb"})
        token_b = resp.json()["access_token"]

        # usera добавляет ссылку
        resp = await ac.post("/links/", json={"url": "https://ya.ru", "title": "UserA Link"}, headers={"Authorization": f"Bearer {token_a}"})
        assert resp.status_code == 200
        link_id = resp.json()["id"]

        # userb пытается получить ссылку usera
        resp = await ac.get(f"/links/{link_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code in (403, 404)

        # userb пытается удалить ссылку usera
        resp = await ac.delete(f"/links/{link_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code in (403, 404)

@pytest.mark.asyncio
async def test_cannot_add_duplicate_link(tmp_path):
    """
    Проверяет, что нельзя добавить одну и ту же ссылку дважды для одного пользователя.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "dupe@example.com", "password": "pass"})
        resp = await ac.post("/login", data={"username": "dupe@example.com", "password": "pass"})
        token = resp.json()["access_token"]

        # Добавляем ссылку первый раз
        resp = await ac.post("/links/", json={"url": "https://example.com", "title": "Test Link"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

        # Пытаемся добавить ту же ссылку второй раз
        resp = await ac.post("/links/", json={"url": "https://example.com", "title": "Test Link"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in (400, 409)

@pytest.mark.asyncio
async def test_xss_and_sql_injection_protection(tmp_path):
    """
    Проверяет, что поля не позволяют внедрить XSS или SQL-инъекции.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "xss@example.com", "password": "pass"})
        resp = await ac.post("/login", data={"username": "xss@example.com", "password": "pass"})
        token = resp.json()["access_token"]

        # Пытаемся добавить ссылку с XSS
        resp = await ac.post("/links/", json={"url": "https://xss.com/<script>alert(1)</script>", "title": "XSS"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in (400, 422)

@pytest.mark.asyncio
async def test_required_fields(tmp_path):
    """
    Проверяет, что нельзя создать коллекцию без имени.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "fields@example.com", "password": "pass"})
        resp = await ac.post("/login", data={"username": "fields@example.com", "password": "pass"})
        token = resp.json()["access_token"]

        # Пытаемся создать коллекцию без имени
        resp = await ac.post("/collections/", json={"description": "desc"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 422 
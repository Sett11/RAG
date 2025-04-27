"""
Тесты для проверки операций с коллекциями: создание, получение, обновление, удаление.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_collections_crud():
    """
    Проверяет полный цикл работы с коллекциями для пользователя.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Регистрация и вход
        await ac.post("/register", json={"email": "colluser@example.com", "password": "collpass"})
        login_resp = await ac.post("/login", data={"username": "colluser@example.com", "password": "collpass"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Создание новой коллекции
        coll_data = {"name": "Мои ссылки", "description": "Коллекция для теста"}
        resp = await ac.post("/collections/", json=coll_data, headers=headers)
        assert resp.status_code == 200
        coll = resp.json()
        assert coll["name"] == "Мои ссылки"
        coll_id = coll["id"]

        # Получение списка коллекций
        resp = await ac.get("/collections/", headers=headers)
        assert resp.status_code == 200
        colls = resp.json()
        assert any(c["id"] == coll_id for c in colls)

        # Обновление коллекции
        update_data = {"name": "Изменённая коллекция", "description": "Новое описание"}
        resp = await ac.put(f"/collections/{coll_id}", json=update_data, headers=headers)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["name"] == "Изменённая коллекция"
        assert updated["description"] == "Новое описание"

        # Удаление коллекции
        resp = await ac.delete(f"/collections/{coll_id}", headers=headers)
        assert resp.status_code == 200
        assert "Collection deleted successfully" in resp.text

        # Проверка, что коллекция удалена
        resp = await ac.get("/collections/", headers=headers)
        assert all(c["id"] != coll_id for c in resp.json())

        # Попытка обновить несуществующую коллекцию
        resp = await ac.put(f"/collections/{coll_id}", json=update_data, headers=headers)
        assert resp.status_code == 404

        # Попытка удалить несуществующую коллекцию
        resp = await ac.delete(f"/collections/{coll_id}", headers=headers)
        assert resp.status_code == 404 
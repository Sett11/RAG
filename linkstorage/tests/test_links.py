"""
Тесты для проверки операций со ссылками: создание, получение, обновление, удаление.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_links_crud():
    """
    Проверяет полный цикл работы со ссылками для пользователя.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Регистрация и вход
        await ac.post("/register", json={"email": "linkuser@example.com", "password": "linkpass"})
        login_resp = await ac.post("/login", data={"username": "linkuser@example.com", "password": "linkpass"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Создание новой ссылки
        link_data = {
            "title": "Google",
            "description": "Search engine",
            "url": "https://www.google.com",
            "image": "https://www.google.com/logo.png",
            "link_type": "website"
        }
        resp = await ac.post("/links/", json=link_data, headers=headers)
        assert resp.status_code == 200
        link = resp.json()
        assert link["title"] == "Google"
        link_id = link["id"]

        # Получение списка ссылок
        resp = await ac.get("/links/", headers=headers)
        assert resp.status_code == 200
        links = resp.json()
        assert any(l["id"] == link_id for l in links)

        # Обновление ссылки
        update_data = {"title": "Google Search", "description": "The best search engine"}
        resp = await ac.put(f"/links/{link_id}", json=update_data, headers=headers)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["title"] == "Google Search"
        assert updated["description"] == "The best search engine"

        # Удаление ссылки
        resp = await ac.delete(f"/links/{link_id}", headers=headers)
        assert resp.status_code == 200
        assert "Link deleted successfully" in resp.text

        # Проверка, что ссылка удалена
        resp = await ac.get("/links/", headers=headers)
        assert all(l["id"] != link_id for l in resp.json())

        # Попытка обновить несуществующую ссылку
        resp = await ac.put(f"/links/{link_id}", json=update_data, headers=headers)
        assert resp.status_code == 404

        # Попытка удалить несуществующую ссылку
        resp = await ac.delete(f"/links/{link_id}", headers=headers)
        assert resp.status_code == 404 
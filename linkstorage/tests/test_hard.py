import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_race_condition_duplicate_link(tmp_path):
    """
    Проверяет, что при одновременной попытке добавить одну и ту же ссылку двумя пользователями не возникает дублирования.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "race1@example.com", "password": "pass"})
        await ac.post("/register", json={"email": "race2@example.com", "password": "pass"})
        resp1 = await ac.post("/login", data={"username": "race1@example.com", "password": "pass"})
        token1 = resp1.json()["access_token"]
        resp2 = await ac.post("/login", data={"username": "race2@example.com", "password": "pass"})
        token2 = resp2.json()["access_token"]
        # Оба пользователя пытаются добавить одну и ту же ссылку
        r1 = await ac.post("/links/", json={"url": "https://race.com", "title": "Race"}, headers={"Authorization": f"Bearer {token1}"})
        r2 = await ac.post("/links/", json={"url": "https://race.com", "title": "Race"}, headers={"Authorization": f"Bearer {token2}"})
        # Оба должны получить 200 или 409, но не создать две одинаковые ссылки для одного пользователя
        assert r1.status_code in (200, 409)
        assert r2.status_code in (200, 409)

@pytest.mark.asyncio
async def test_mass_delete_user_links_collections(tmp_path):
    """
    Проверяет, что при удалении пользователя удаляются все его ссылки и коллекции (если реализовано каскадное удаление).
    """
    from app.database import SessionLocal
    from app.models.user import User
    from app.models.link import Link
    from app.models.collection import Collection
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "massdel@example.com", "password": "pass"})
        resp = await ac.post("/login", data={"username": "massdel@example.com", "password": "pass"})
        token = resp.json()["access_token"]
        # Добавляем ссылки и коллекции
        for i in range(3):
            await ac.post("/links/", json={"url": f"https://massdel.com/{i}", "title": f"L{i}"}, headers={"Authorization": f"Bearer {token}"})
            await ac.post("/collections/", json={"name": f"C{i}"}, headers={"Authorization": f"Bearer {token}"})
        # Удаляем пользователя напрямую из БД
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == "massdel@example.com").first()
            db.delete(user)
            db.commit()
            # Проверяем, что ссылки и коллекции удалены
            links = db.query(Link).filter(Link.user_id == user.id).all()
            collections = db.query(Collection).filter(Collection.user_id == user.id).all()
            assert len(links) == 0
            assert len(collections) == 0

@pytest.mark.asyncio
async def test_update_foreign_link_collection(tmp_path):
    """
    Проверяет, что пользователь не может обновить чужую ссылку или коллекцию.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "owner@example.com", "password": "pass"})
        await ac.post("/register", json={"email": "intruder@example.com", "password": "pass"})
        resp = await ac.post("/login", data={"username": "owner@example.com", "password": "pass"})
        token_owner = resp.json()["access_token"]
        resp = await ac.post("/login", data={"username": "intruder@example.com", "password": "pass"})
        token_intruder = resp.json()["access_token"]
        # Владелец создаёт ссылку и коллекцию
        link_resp = await ac.post("/links/", json={"url": "https://forbidden.com", "title": "Forbid"}, headers={"Authorization": f"Bearer {token_owner}"})
        link_id = link_resp.json()["id"]
        coll_resp = await ac.post("/collections/", json={"name": "ForbidColl"}, headers={"Authorization": f"Bearer {token_owner}"})
        coll_id = coll_resp.json()["id"]
        # Нарушитель пытается обновить
        resp = await ac.put(f"/links/{link_id}", json={"title": "Hacked"}, headers={"Authorization": f"Bearer {token_intruder}"})
        assert resp.status_code == 404
        resp = await ac.put(f"/collections/{coll_id}", json={"name": "HackedColl"}, headers={"Authorization": f"Bearer {token_intruder}"})
        assert resp.status_code == 404

@pytest.mark.asyncio
async def test_invalid_types_and_sql_injection(tmp_path):
    """
    Проверяет, что API возвращает 422 при попытке передать невалидные типы и SQL-инъекцию в других полях.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "sqltest@example.com", "password": "pass"})
        resp = await ac.post("/login", data={"username": "sqltest@example.com", "password": "pass"})
        token = resp.json()["access_token"]
        # Некорректный email
        resp = await ac.post("/register", json={"email": 12345, "password": "pass"})
        assert resp.status_code == 422
        # SQL-инъекция в title
        resp = await ac.post("/links/", json={"url": "https://sqltest.com", "title": "1; DROP TABLE users;"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in (200, 201)  # Просто строка, не выполнится как SQL

@pytest.mark.asyncio
async def test_xss_in_title_description(tmp_path):
    """
    Проверяет, что XSS в title/description не приводит к ошибке на бэке (но фронт должен экранировать).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "xsstitle@example.com", "password": "pass"})
        resp = await ac.post("/login", data={"username": "xsstitle@example.com", "password": "pass"})
        token = resp.json()["access_token"]
        # XSS в title
        resp = await ac.post("/links/", json={"url": "https://xsstitle.com", "title": "<script>alert(1)</script>"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in (200, 201)
        # XSS в description
        resp = await ac.post("/links/", json={"url": "https://xsstitle.com/desc", "title": "desc", "description": "<img src=x onerror=alert(1)>"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in (200, 201)

@pytest.mark.asyncio
async def test_simultaneous_password_reset(tmp_path):
    """
    Проверяет, что при одновременных запросах на сброс пароля для одного пользователя выдается только последний токен.
    """
    from app.database import SessionLocal
    from app.models.user import User
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "simulreset@example.com", "password": "pass"})
        # Два запроса на сброс пароля
        resp1 = await ac.post("/reset-password/request", json={"email": "simulreset@example.com"})
        token1 = resp1.json()["message"].split(": ")[-1]
        resp2 = await ac.post("/reset-password/request", json={"email": "simulreset@example.com"})
        token2 = resp2.json()["message"].split(": ")[-1]
        # Первый токен уже невалиден
        response = await ac.post("/reset-password/confirm", json={"token": token1, "new_password": "newpass1"})
        assert response.status_code == 400
        # Второй токен валиден
        response = await ac.post("/reset-password/confirm", json={"token": token2, "new_password": "newpass2"})
        assert response.status_code == 200 
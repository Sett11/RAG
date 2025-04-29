import pytest
import time
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_bulk_links_performance(tmp_path):
    """
    Проверяет производительность массового добавления ссылок (1000 штук).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/register", json={"email": "perf@example.com", "password": "pass"})
        resp = await ac.post("/login", data={"username": "perf@example.com", "password": "pass"})
        token = resp.json()["access_token"]
        start = time.time()
        for i in range(1000):
            r = await ac.post(
                "/links/",
                json={"url": f"https://perf.com/{i}", "title": f"Perf {i}"},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert r.status_code in (200, 201, 409)
        elapsed = time.time() - start
        print(f"Добавление 1000 ссылок заняло {elapsed:.2f} секунд")
        assert elapsed < 60  # Ожидаем, что тест пройдёт за минуту 
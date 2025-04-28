import pytest
from app.database import SessionLocal
from app.models.user import User
from app.models.link import Link
from app.models.collection import Collection

@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Link).delete()
    db.query(Collection).delete()
    db.query(User).delete()
    db.commit()
    db.close() 
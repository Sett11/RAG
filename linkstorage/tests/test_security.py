import pytest
from jose import jwt
from fastapi import HTTPException, status
from app.utils import security
from app.models.user import User
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

SECRET_KEY = security.SECRET_KEY
ALGORITHM = security.ALGORITHM


def test_get_current_user_invalid_token():
    db = MagicMock(spec=Session)
    invalid_token = "invalid.token.value"
    with pytest.raises(HTTPException) as excinfo:
        security.get_current_user(token=invalid_token, db=db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in excinfo.value.detail


def test_get_current_user_token_without_email():
    db = MagicMock(spec=Session)
    # Создаём токен без sub/email
    token = jwt.encode({"some": "data"}, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as excinfo:
        security.get_current_user(token=token, db=db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in excinfo.value.detail


def test_get_current_user_user_not_found():
    db = MagicMock(spec=Session)
    # Создаём токен с sub/email
    token = jwt.encode({"sub": "notfound@example.com"}, SECRET_KEY, algorithm=ALGORITHM)
    db.query().filter().first.return_value = None
    with pytest.raises(HTTPException) as excinfo:
        security.get_current_user(token=token, db=db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in excinfo.value.detail


def test_change_password_user_not_found():
    db = MagicMock(spec=Session)
    user = MagicMock(spec=User)
    user.id = 999
    db.query().filter().first.return_value = None
    with pytest.raises(HTTPException) as excinfo:
        security.change_password(db, user, "newpass")
    assert excinfo.value.status_code == 404
    assert "User not found" in excinfo.value.detail 
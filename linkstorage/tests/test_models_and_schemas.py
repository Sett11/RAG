import os
import pytest
from app.models.collection import CollectionLink
from app.schemas.collection import CollectionResponse
from app.schemas.link import LinkResponse
from app.schemas.user import UserResponse, Token
from app.utils.mylogger import ensure_log_directory


def test_collection_link_init():
    link = CollectionLink(collection_id=1, link_id=2)
    assert link.collection_id == 1
    assert link.link_id == 2


def test_collection_response_init():
    obj = CollectionResponse(id=1, user_id=2, name='Test', description='Desc')
    assert obj.id == 1
    assert obj.name == 'Test'


def test_link_response_init():
    obj = LinkResponse(id=1, user_id=2, title='T', url='https://a.ru', link_type='website')
    assert obj.id == 1
    assert str(obj.url) == 'https://a.ru/'


def test_user_response_init():
    obj = UserResponse(id=1, email='a@b.com', is_active=True)
    assert obj.id == 1
    assert obj.email == 'a@b.com'


def test_token_init():
    obj = Token(access_token='abc', token_type='bearer')
    assert obj.access_token == 'abc'
    assert obj.token_type == 'bearer'


def test_ensure_log_directory(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    monkeypatch.setattr("app.utils.mylogger.os.path.exists", lambda path: False)
    monkeypatch.setattr("app.utils.mylogger.os.makedirs", lambda path: log_dir.mkdir())
    ensure_log_directory()
    assert log_dir.exists() or os.path.exists("logs") 
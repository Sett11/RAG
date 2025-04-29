import pytest
from unittest.mock import patch, Mock
from app.utils.link_parser import parse_link_metadata


def test_parse_link_metadata_success():
    html = '''
    <html>
        <head>
            <meta property="og:title" content="Test Title">
            <meta property="og:description" content="Test Description">
            <meta property="og:image" content="http://example.com/image.png">
            <meta property="og:type" content="website">
        </head>
        <body></body>
    </html>
    '''
    mock_response = Mock()
    mock_response.text = html
    mock_response.raise_for_status = Mock()
    with patch("app.utils.link_parser.requests.get", return_value=mock_response):
        metadata = parse_link_metadata("http://example.com")
        assert metadata["title"] == "Test Title"
        assert metadata["description"] == "Test Description"
        assert metadata["image"] == "http://example.com/image.png"
        assert metadata["link_type"] == "website"


def test_parse_link_metadata_no_og_tags():
    html = '''
    <html>
        <head>
            <title>Simple Title</title>
            <meta name="description" content="Simple Description">
        </head>
        <body></body>
    </html>
    '''
    mock_response = Mock()
    mock_response.text = html
    mock_response.raise_for_status = Mock()
    with patch("app.utils.link_parser.requests.get", return_value=mock_response):
        metadata = parse_link_metadata("http://example.com")
        assert metadata["title"] == "Simple Title"
        assert metadata["description"] == "Simple Description"
        assert metadata["image"] is None
        assert metadata["link_type"] == "website"


def test_parse_link_metadata_request_error():
    with patch("app.utils.link_parser.requests.get", side_effect=Exception("Network error")):
        metadata = parse_link_metadata("http://example.com")
        assert metadata is None 
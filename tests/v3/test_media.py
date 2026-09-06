"""Media service tests with mocked multipart HTTP."""

import httpx
import pytest

from whatsloon.config.settings import RetryConfig, TimeoutConfig
from whatsloon.exceptions import ValidationError
from whatsloon.media.service import MediaService
from whatsloon.transport.sync import SyncTransport


def _service(monkeypatch, handler):
    """Build a media service over a mocked transport.

    Args:
        monkeypatch: Pytest fixture.
        handler: Fake httpx request handler.

    Returns:
        MediaService instance.
    """
    transport = SyncTransport(
        base_url="https://graph.facebook.com/v26.0",
        access_token="secret",
        timeout=TimeoutConfig(),
        retry=RetryConfig(max_attempts=1, jitter=False),
    )

    def fake_request(self, method, url, **kwargs):
        return handler(method, url, kwargs)

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    return MediaService(transport, "123")


def _ok(data):
    """Build a minimal JSON response double.

    Args:
        data: JSON body.

    Returns:
        httpx response.
    """
    request = httpx.Request("POST", "https://graph.facebook.com/v26.0/x")
    return httpx.Response(200, json=data, request=request)


def test_upload_bytes_sends_multipart(monkeypatch):
    """Uploads post multipart with messaging_product and file fields."""
    seen = {}

    def handler(method, url, kwargs):
        seen.update(method=method, url=url, kwargs=kwargs)
        return _ok({"id": "mid-1"})

    service = _service(monkeypatch, handler)
    result = service.upload_bytes(b"bytes", "image/jpeg", filename="a.jpg")
    assert result.media_id == "mid-1"
    assert seen["url"] == "https://graph.facebook.com/v26.0/123/media"
    assert kwargs_files(seen)["file"][0] == "a.jpg"
    assert seen["kwargs"]["data"] == {"messaging_product": "whatsapp", "type": "image/jpeg"}
    assert "Content-Type" not in seen["kwargs"]["headers"]


def kwargs_files(seen):
    """Extract files from captured kwargs.

    Args:
        seen: Captured call mapping.

    Returns:
        Files mapping.
    """
    return seen["kwargs"]["files"]


def test_upload_validation(monkeypatch):
    """Empty content and bad MIME types fail before HTTP."""
    service = _service(monkeypatch, lambda m, u, k: _ok({}))
    with pytest.raises(ValidationError):
        service.upload_bytes(b"", "image/jpeg")
    with pytest.raises(ValidationError):
        service.upload_bytes(b"x", "not-a-mime")
    with pytest.raises(ValidationError):
        service.upload_file("does-not-exist.jpg", "image/jpeg")


def test_get_url_download_delete(monkeypatch):
    """URL retrieval, download, and deletion follow Meta contracts."""
    calls = []

    def handler(method, url, kwargs):
        calls.append((method, url))
        if url.endswith("/mid-1") and method == "GET":
            return _ok(
                {
                    "id": "mid-1",
                    "url": "https://media.example/x",
                    "mime_type": "image/jpeg",
                    "sha256": "abc",
                    "file_size": 3,
                    "messaging_product": "whatsapp",
                }
            )
        if url == "https://media.example/x":
            request = httpx.Request("GET", url)
            return httpx.Response(200, content=b"img", request=request)
        return _ok({"success": True})

    service = _service(monkeypatch, handler)
    info = service.get_url("mid-1")
    assert info.url == "https://media.example/x" and info.file_size == 3
    download = service.download("mid-1")
    assert download.content == b"img" and download.mime_type == "image/jpeg"
    assert service.delete("mid-1") is True
    assert calls[0] == ("GET", "https://graph.facebook.com/v26.0/mid-1")
    assert calls[1] == ("GET", "https://graph.facebook.com/v26.0/mid-1")
    assert calls[2][0] == "GET" and calls[2][1] == "https://media.example/x"

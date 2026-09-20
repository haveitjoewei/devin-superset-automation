"""GitHub webhook signature verification."""
import hmac
import hashlib
from api import verify_github_signature


def _sign(body: bytes, secret: str = "testsecret") -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_passes():
    body = b'{"hello":"world"}'
    assert verify_github_signature(body, _sign(body)) is True


def test_tampered_body_fails():
    body = b'{"hello":"world"}'
    sig = _sign(body)
    assert verify_github_signature(b'{"hello":"evil"}', sig) is False


def test_missing_signature_fails():
    assert verify_github_signature(b"x", None) is False

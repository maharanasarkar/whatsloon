"""Flows encryption tests against independently built ciphertext."""

import base64
import json
import os

import pytest

cryptography = pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from whatsloon.exceptions import InvalidPayloadError
from whatsloon.flows.crypto import (
    FlowSession,
    decrypt_request,
    encrypt_response,
    generate_keypair,
)


def _meta_style_encrypt(public_pem, body):
    """Encrypt like Meta: RSA-wrapped key + AES-GCM payload.

    Args:
        public_pem: RSA public key PEM.
        body: JSON-serializable request body.

    Returns:
        Tuple of (flow_data_b64, aes_key_b64, iv_b64, aes_key, iv).
    """
    public_key = serialization.load_pem_public_key(public_pem.encode())
    aes_key = os.urandom(16)
    iv = os.urandom(16)
    wrapped = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    encryptor = Cipher(algorithms.AES(aes_key), modes.GCM(iv)).encryptor()
    ciphertext = encryptor.update(json.dumps(body).encode()) + encryptor.finalize()
    return (
        base64.b64encode(ciphertext + encryptor.tag).decode(),
        base64.b64encode(wrapped).decode(),
        base64.b64encode(iv).decode(),
        aes_key,
        iv,
    )


def test_decrypt_meta_style_request():
    """Decryption handles Meta-constructed ciphertext and keys."""
    private_pem, public_pem = generate_keypair()
    body = {"version": "3.0", "action": "ping", "flow_token": "tok"}
    flow_data, aes_key_b64, iv_b64, aes_key, iv = _meta_style_encrypt(public_pem, body)
    decrypted, out_key, out_iv = decrypt_request(flow_data, aes_key_b64, iv_b64, private_pem)
    assert decrypted == body
    assert out_key == aes_key and out_iv == iv


def test_encrypt_response_uses_flipped_iv():
    """Responses decrypt with the bit-inverted IV per Meta spec."""
    private_pem, public_pem = generate_keypair()
    body = {"version": "3.0", "action": "INIT"}
    flow_data, aes_key_b64, iv_b64, aes_key, iv = _meta_style_encrypt(public_pem, body)
    _, out_key, out_iv = decrypt_request(flow_data, aes_key_b64, iv_b64, private_pem)
    encoded = encrypt_response({"screen": "WELCOME"}, out_key, out_iv)
    raw = base64.b64decode(encoded)
    flipped = bytes(byte ^ 0xFF for byte in iv)
    decryptor = Cipher(algorithms.AES(aes_key), modes.GCM(flipped, raw[-16:])).decryptor()
    clear = decryptor.update(raw[:-16]) + decryptor.finalize()
    assert json.loads(clear) == {"screen": "WELCOME"}


def test_flow_session_roundtrip():
    """FlowSession encrypts responses for its own keys."""
    private_pem, public_pem = generate_keypair()
    body = {"action": "data_exchange"}
    flow_data, aes_key_b64, iv_b64, _, _ = _meta_style_encrypt(public_pem, body)
    decrypted, key, iv = decrypt_request(flow_data, aes_key_b64, iv_b64, private_pem)
    session = FlowSession(body=decrypted, aes_key=key, iv=iv)
    assert session.body == body
    assert isinstance(session.encrypt({"ok": True}), str)


def test_tampered_ciphertext_rejected():
    """Modified payloads fail authentication instead of decrypting."""
    private_pem, public_pem = generate_keypair()
    flow_data, aes_key_b64, iv_b64, _, _ = _meta_style_encrypt(public_pem, {"a": 1})
    tampered = base64.b64encode(base64.b64decode(flow_data)[:-17] + b"\x00").decode()
    with pytest.raises(InvalidPayloadError):
        decrypt_request(tampered, aes_key_b64, iv_b64, private_pem)
    with pytest.raises(InvalidPayloadError):
        decrypt_request(flow_data, aes_key_b64, iv_b64, "not-a-key")

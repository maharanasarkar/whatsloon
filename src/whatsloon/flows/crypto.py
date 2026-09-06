"""WhatsApp Flows endpoint encryption (``whatsloon[flows]`` extra).

Implements Meta's Data Exchange encryption exactly as documented in the
official endpoint guide: RSA-OAEP-SHA256 unwraps the 128-bit payload key,
AES-GCM decrypts the request (tag = trailing 16 bytes), and responses are
AES-GCM encrypted with the bit-inverted IV (each byte XOR ``0xFF``), tag
appended, base64-encoded.

Reference: https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint/
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any as _Any
from typing import Optional, Union

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Flows encryption requires the 'flows' extra: pip install 'whatsloon[flows]'."
    ) from exc

TAG_LENGTH = 16
"""AES-GCM authentication tag length in bytes."""


def _b64decode(value: str) -> bytes:
    """Decode base64, raising a typed error on failure.

    Args:
        value: Base64 string.

    Returns:
        Decoded bytes.

    Raises:
        InvalidPayloadError: If decoding fails.
    """
    from whatsloon.exceptions import InvalidPayloadError

    try:
        return base64.b64decode(value)
    except Exception as exc:
        raise InvalidPayloadError("Flow payload is not valid base64.") from exc


def generate_keypair(*, key_size: int = 2048) -> tuple[str, str]:
    """Generate an RSA keypair for Flow endpoints.

    Args:
        key_size: RSA key size in bits.

    Returns:
        Tuple of (private PEM, public PEM). Guard the private key.
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode("utf-8")
    )
    return private_pem, public_pem


def decrypt_request(
    encrypted_flow_data_b64: str,
    encrypted_aes_key_b64: str,
    initial_vector_b64: str,
    private_key_pem: Union[str, bytes],
    *,
    passphrase: Optional[bytes] = None,
) -> tuple[dict[str, _Any], bytes, bytes]:
    """Decrypt a Flow data-exchange request.

    Args:
        encrypted_flow_data_b64: Base64 AES-GCM ciphertext with appended tag.
        encrypted_aes_key_b64: Base64 RSA-wrapped 128-bit AES key.
        initial_vector_b64: Base64 initialization vector.
        private_key_pem: PEM private key matching the uploaded public key.
        passphrase: Private key passphrase, if encrypted.

    Returns:
        Tuple of (decrypted body, AES key bytes, IV bytes) for reuse when
        encrypting the response.

    Raises:
        InvalidPayloadError: If decryption or authentication fails.
    """
    from whatsloon.exceptions import InvalidPayloadError

    pem = private_key_pem.encode("utf-8") if isinstance(private_key_pem, str) else private_key_pem
    try:
        loaded = serialization.load_pem_private_key(pem, password=passphrase)
        if not isinstance(loaded, rsa.RSAPrivateKey):
            raise InvalidPayloadError("Flow private key must be RSA.")
        private_key = loaded
        aes_key = private_key.decrypt(
            _b64decode(encrypted_aes_key_b64),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        flow_data = _b64decode(encrypted_flow_data_b64)
        iv = _b64decode(initial_vector_b64)
        body, tag = flow_data[:-TAG_LENGTH], flow_data[-TAG_LENGTH:]
        decryptor = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag)).decryptor()
        clear = decryptor.update(body) + decryptor.finalize()
        return json.loads(clear.decode("utf-8")), aes_key, iv
    except InvalidPayloadError:
        raise
    except Exception as exc:
        raise InvalidPayloadError("Flow request decryption failed.") from exc


def encrypt_response(response: dict[str, _Any], aes_key: bytes, iv: bytes) -> str:
    """Encrypt a Flow response with the request key and inverted IV.

    Args:
        response: JSON-serializable response payload.
        aes_key: AES key unwrapped from the request.
        iv: Request initialization vector; bits are inverted per Meta spec.

    Returns:
        Base64 ciphertext with appended tag, sent as plain text.
    """
    flipped = bytearray(byte ^ 0xFF for byte in iv)
    encryptor = Cipher(algorithms.AES(aes_key), modes.GCM(bytes(flipped))).encryptor()
    ciphertext = encryptor.update(json.dumps(response).encode("utf-8")) + encryptor.finalize()
    return base64.b64encode(ciphertext + encryptor.tag).decode("utf-8")


@dataclass
class FlowSession:
    """Decrypted request context for building a response.

    Attributes:
        body: Decrypted request body.
        aes_key: Payload encryption key for the response.
        iv: Request initialization vector.
    """

    body: dict[str, _Any]
    aes_key: bytes
    iv: bytes

    def encrypt(self, response: dict[str, _Any]) -> str:
        """Encrypt a response for this session.

        Args:
            response: JSON-serializable response payload.

        Returns:
            Base64 response body.
        """
        return encrypt_response(response, self.aes_key, self.iv)


__all__ = [
    "TAG_LENGTH",
    "FlowSession",
    "decrypt_request",
    "encrypt_response",
    "generate_keypair",
]

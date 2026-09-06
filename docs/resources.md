# Media, templates, business, and Flows

## Media (`wa.media`)

```python
upload = wa.media.upload_file("photo.jpg", "image/jpeg")
info = wa.media.get_url(upload.media_id)
data = wa.media.download(upload.media_id)
wa.media.delete(upload.media_id)
```

Uploads use multipart over the shared pooled transport; downloads reuse the
temporary Meta URL (bearer-authenticated, ~5-minute expiry).

## Templates (`wa.templates`)

```python
templates = wa.templates.list_templates("WABA_ID")
created = wa.templates.create_template("WABA_ID", TemplateSpec(name="hello", language="en_US"))
wa.templates.delete_template("WABA_ID", "hello")
```

## Business (`wa.business`)

```python
account = wa.business.get_account("WABA_ID")
numbers = wa.business.list_phone_numbers("WABA_ID")
wa.business.register_phone("PHONE_ID", pin="123456")
```

## Flows encryption (`whatsloon[flows]`)

Implements Meta's Data Exchange encryption (RSA-OAEP-SHA256 + AES-GCM,
bit-inverted response IV):

```python
from whatsloon.flows.crypto import FlowSession, decrypt_request, generate_keypair

private_pem, public_pem = generate_keypair()  # upload public_pem to Meta
body, aes_key, iv = decrypt_request(flow_data, aes_key_b64, iv_b64, private_pem)
session = FlowSession(body=body, aes_key=aes_key, iv=iv)
encrypted = session.encrypt({"screen": "SUCCESS", "data": {}})
```

See `examples/v3_resources.py` and `examples/v3_flow_endpoint.py`.

import os, json
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

ISSUER_DID = os.getenv("ISSUER_DID", "did:web:openline.local")
_hex = os.getenv("SIGNING_SK_HEX", None)
if _hex and len(_hex) >= 64:
    _SK = SigningKey(_hex, encoder=HexEncoder)
else:
    _SK = SigningKey.generate()  # dev/CI only

def canonical_bytes(payload: dict) -> bytes:
    if "sig" in payload:
        payload = {k: v for k, v in payload.items() if k != "sig"}
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

def sign_fields(payload: dict) -> str:
    return _SK.sign(canonical_bytes(payload)).signature.hex()

# server.py — minimal, ASCII-only, CI-friendly
import os, json, hashlib, time
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, Body, HTTPException
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

# --- config (env) ---
ISSUER_DID = os.getenv("ISSUER_DID", "did:web:openline.local")
DEV_SEED   = os.getenv("DEV_SEED", "dev-seed-change-me-32bytes________")
KEY_ID     = os.getenv("KEY_ID", "dev-1")

# --- key from seed (deterministic dev key) ---
def seed_to_sk(seed: str) -> SigningKey:
    seed_bytes = hashlib.blake2b(seed.encode("utf-8"), digest_size=32).digest()
    return SigningKey(seed_bytes)

SK = seed_to_sk(DEV_SEED)
PK_HEX = SK.verify_key.encode(encoder=HexEncoder).decode()

# --- helpers ---
def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def sort_keys_deep(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: sort_keys_deep(x[k]) for k in sorted(x.keys())}
    if isinstance(x, list):
        return [sort_keys_deep(v) for v in x]
    return x

def sign_fields(obj: Dict[str, Any]) -> str:
    # sign canonical JSON without "sig"
    to_sign = dict(obj)
    if "sig" in to_sign:
        del to_sign["sig"]
    msg = json.dumps(sort_keys_deep(to_sign), separators=(",", ":"), ensure_ascii=True).encode()
    return SK.sign(msg).signature.hex()

def ensure_file(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)

def save_receipt(dirpath: str, rec: Dict[str, Any]) -> None:
    os.makedirs(dirpath, exist_ok=True)
    with open(f"{dirpath}/{rec['rid']}.json", "w") as f:
        json.dump(rec, f, indent=2, sort_keys=True)
    # latest pointer for Pages demo
    ensure_file("docs/receipt.latest.json", rec)
    # publish public key if missing
    pub_path = "docs/issuer.pub.json"
    if not os.path.exists(pub_path):
        ensure_file(pub_path, {
            "issuer": ISSUER_DID,
            "kid": KEY_ID,
            "ed25519_public_key_hex": PK_HEX
        })

# --- FastAPI app ---
app = FastAPI(title="OpenLine Amber Demo")

@app.get("/health")
def health():
    return {"ok": True, "issuer": ISSUER_DID, "kid": KEY_ID}

# ---------- AMBER LOOP ENDPOINTS (content-minimal receipts) ----------

@app.post("/api/amber/capture")
def amber_capture(payload: Dict[str, Any] = Body(...)):
    rid = "ar_" + now_iso().replace(":", "-") + "_" + str(int(time.time()))[-4:]
    rec = {
        "rid": rid,
        "when": now_iso(),
        "issuer": ISSUER_DID,
        "where": {"host": "api", "coarse": "device:server"},
        "what": {"badge": "amber", "kind": "case"},
        "flags": payload.get("flags", ["amber:unconfirmed", "route:experiment"]),
        "metrics": payload.get("metrics", {}),
        "digests": payload.get("digests", {}),
        "kid": KEY_ID,
        "schema": "olr/ar.v0.1",
    }
    rec["sig"] = sign_fields(rec)
    save_receipt("docs/receipts/amber", rec)
    return {"receipt": rec}

@app.post("/api/amber/eval")
def amber_eval(payload: Dict[str, Any] = Body(...)):
    parent = payload.get("parent")
    if not parent:
        raise HTTPException(400, "parent required")
    rid = "evr_" + now_iso().replace(":", "-") + "_" + str(int(time.time()))[-4:]
    rec = {
        "rid": rid,
        "parent": parent,
        "when": now_iso(),
        "issuer": ISSUER_DID,
        "what": {"badge": "eval", "kind": "variant"},
        "variant": payload.get("variant", {}),
        "tests": payload.get("tests", []),
        "metrics": payload.get("metrics", {}),
        "schema": "olr/evr.v0.1",
        "kid": KEY_ID,
    }
    rec["sig"] = sign_fields(rec)
    save_receipt("docs/receipts/eval", rec)
    return {"receipt": rec}

@app.post("/api/amber/label")
def amber_label(payload: Dict[str, Any] = Body(...)):
    parent = payload.get("parent")
    if not parent:
        raise HTTPException(400, "parent required")
    rid = "lbr_" + now_iso().replace(":", "-") + "_" + str(int(time.time()))[-4:]
    rec = {
        "rid": rid,
        "parent": parent,
        "when": now_iso(),
        "issuer": ISSUER_DID,
        "what": {"badge": "label", "kind": "adjudication"},
        "label": payload.get("label", {}),
        "schema": "olr/lbr.v0.1",
        "kid": KEY_ID,
    }
    rec["sig"] = sign_fields(rec)
    save_receipt("docs/receipts/label", rec)
    return {"receipt": rec}

@app.post("/api/amber/promote")
def amber_promote(payload: Dict[str, Any] = Body(...)):
    parent = payload.get("parent")
    if not parent:
        raise HTTPException(400, "parent required")
    rid = "gpr_" + now_iso().replace(":", "-") + "_" + str(int(time.time()))[-4:]
    rec = {
        "rid": rid,
        "parent": parent,
        "when": now_iso(),
        "issuer": ISSUER_DID,
        "what": {"badge": "gold", "kind": "promotion"},
        "basis": payload.get("basis", {}),
        "policy_checks": payload.get("policy_checks", {}),
        "schema": "olr/gpr.v0.1",
        "kid": KEY_ID,
    }
    rec["sig"] = sign_fields(rec)
    save_receipt("docs/receipts/promote", rec)
    return {"receipt": rec}

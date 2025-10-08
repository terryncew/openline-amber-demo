from fastapi import APIRouter, Body, HTTPException
from datetime import datetime, timezone
import uuid, os, json
from receipts_signing import sign_fields, ISSUER_DID

router = APIRouter()

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def save(dirpath: str, rec: dict):
    os.makedirs(dirpath, exist_ok=True)
    with open(f"{dirpath}/{rec['rid']}.json","w") as f: json.dump(rec, f, indent=2, sort_keys=True)
    with open("docs/receipt.latest.json","w") as f: json.dump(rec, f, indent=2, sort_keys=True)

@router.post("/amber/capture")
def amber_capture(payload: dict = Body(...)):
    rid = f"ar_{now().replace(':','-')}_{uuid.uuid4().hex[:4]}"
    rec = {
        "rid": rid, "when": now(), "issuer": ISSUER_DID,
        "where": {"host": os.getenv("HOSTNAME","api"), "coarse":"device:server"},
        "what": {"badge":"amber", "kind":"case"},
        "flags": payload.get("flags", ["amber:unconfirmed","route:experiment"]),
        "metrics": payload.get("metrics", {}),
        "digests": payload.get("digests", {}),
        "triggers": payload.get("triggers", []),  # e.g., ["unconfirmed_ratio","motif_distance"]
        "kid": "dev-1", "schema": "olr/ar.v0.1"
    }
    rec["sig"] = sign_fields(rec)
    save("docs/receipts/amber", rec)
    return {"receipt": rec}

@router.post("/amber/eval")
def amber_eval(payload: dict = Body(...)):
    parent = payload.get("parent")
    if not parent: raise HTTPException(400, "parent required")
    rid = f"evr_{now().replace(':','-')}_{uuid.uuid4().hex[:4]}"
    rec = {
        "rid": rid, "parent": parent, "when": now(), "issuer": ISSUER_DID,
        "what": {"badge":"eval", "kind":"variant"},
        "variant": payload.get("variant", {}),
        "tests": payload.get("tests", []),
        "metrics": payload.get("metrics", {}),
        "schema":"olr/evr.v0.1","kid":"dev-1"
    }
    rec["sig"] = sign_fields(rec)
    save("docs/receipts/eval", rec)
    return {"receipt": rec}

@router.post("/amber/label")
def amber_label(payload: dict = Body(...)):
    parent = payload.get("parent")
    if not parent: raise HTTPException(400, "parent required")
    rid = f"lbr_{now().replace(':','-')}_{uuid.uuid4().hex[:4]}"
    rec = {
        "rid": rid, "parent": parent, "when": now(), "issuer": ISSUER_DID,
        "what": {"badge":"label", "kind":"adjudication"},
        "label": payload.get("label", {}),
        "schema":"olr/lbr.v0.1","kid":"dev-1"
    }
    rec["sig"] = sign_fields(rec)
    save("docs/receipts/label", rec)
    return {"receipt": rec}

@router.post("/amber/promote")
def amber_promote(payload: dict = Body(...)):
    parent = payload.get("parent")
    if not parent: raise HTTPException(400, "parent required")
    rid = f"gpr_{now().replace(':','-')}_{uuid.uuid4().hex[:4]}"
    rec = {
        "rid": rid, "parent": parent, "when": now(), "issuer": ISSUER_DID,
        "what": {"badge":"gold", "kind":"promotion"},
        "basis": payload.get("basis", {}),
        "policy_checks": payload.get("policy_checks", {}),
        "schema":"olr/gpr.v0.1","kid":"dev-1"
    }
    rec["sig"] = sign_fields(rec)
    save("docs/receipts/promote", rec)
    return {"receipt": rec}

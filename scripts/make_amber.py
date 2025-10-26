#!/usr/bin/env python3
import json, pathlib, time

out = {
  "receipt_version": "olr/1.5",
  "attrs": {"status":"amber","ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "run_id": "amber-demo-local"},
  "policy": {"policy_id":"openline/policy.v1","policy_hash":"sha256:6babccff24555fa448e5d0dcfd9c1404cd1d1e8c6ca7c151bc675fd7235f8ed6"},
  "signals": {"kappa": 0.78, "dhol": 0.29, "evidence_strength": 0.33},
  "guards": {"ucr": 0.31, "cycles": 0, "contradictions": 0},
  "telem": {"dials": {"dphi_dk_q8": 140, "d2phi_dt2_q8": 108, "fresh_ratio_q8": 170, "scale":"q8_signed","description":"q8_signed maps [-1..+1] -> [0..255], 128 ≈ 0"}}
}
pathlib.Path("docs").mkdir(parents=True, exist_ok=True)
pathlib.Path("docs/receipt.latest.json").write_text(json.dumps(out, separators=(',',':'), ensure_ascii=False))
print("wrote docs/receipt.latest.json")

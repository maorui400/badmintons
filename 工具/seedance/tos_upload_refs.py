#!/usr/bin/env python3
"""Create a private TOS bucket, upload SHOT-001 refs, and mint signed URLs."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import tos


REPO_ROOT = Path(__file__).resolve().parents[2]
ENDPOINT = "tos-cn-beijing.volces.com"
REGION = "cn-beijing"
URL_TTL_SECONDS = 72 * 60 * 60
STATE_PATH = REPO_ROOT / "\u5236\u4f5c" / "EP01" / "tos_storage.json"
RUNTIME_PATH = (
    REPO_ROOT
    / "\u5236\u4f5c"
    / "EP01"
    / "runtime"
    / "tos_assets.resolved.json"
)

SOURCES = [
    {
        "asset_id": "CHAR-001-TURNAROUND-v003",
        "local_path": "\u4eba\u7269/CHAR-001_\u94c1\u86cb/\u4e09\u89c6\u56fe/CHAR-001_turnaround_v003_COST-B_001.png",
        "object_key": "seedance/EP01/SHOT-001/refs/CHAR-001_turnaround_v003_COST-B_001.png",
    },
    {
        "asset_id": "SHOT-001-KF01-v001",
        "local_path": "\u5206\u955c/SHOT-001_\u5de5\u4f4d\u62c9\u8fdc/\u5173\u952e\u5e27/SHOT-001_KF01_v001.png",
        "object_key": "seedance/EP01/SHOT-001/refs/SHOT-001_KF01_v001.png",
    },
    {
        "asset_id": "SHOT-001-KF02-v001",
        "local_path": "\u5206\u955c/SHOT-001_\u5de5\u4f4d\u62c9\u8fdc/\u5173\u952e\u5e27/SHOT-001_KF02_v001.png",
        "object_key": "seedance/EP01/SHOT-001/refs/SHOT-001_KF02_v001.png",
    },
    {
        "asset_id": "SHOT-001-KF03-v001",
        "local_path": "\u5206\u955c/SHOT-001_\u5de5\u4f4d\u62c9\u8fdc/\u5173\u952e\u5e27/SHOT-001_KF03_v001.png",
        "object_key": "seedance/EP01/SHOT-001/refs/SHOT-001_KF03_v001.png",
    },
]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_or_make_bucket_name() -> str:
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if state.get("bucket"):
            return state["bucket"]
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"badmintons-seedance-ep01-{date_part}-{secrets.token_hex(4)}"


def main() -> int:
    ak = os.environ.get("TOS_ACCESS_KEY", "").strip()
    sk = os.environ.get("TOS_SECRET_KEY", "").strip()
    if not ak or not sk:
        raise RuntimeError("TOS credentials are not available in this process.")

    for source in SOURCES:
        local = REPO_ROOT / source["local_path"]
        if not local.is_file():
            raise FileNotFoundError(local)

    client = tos.TosClientV2(ak, sk, ENDPOINT, REGION)
    bucket = load_or_make_bucket_name()
    if not STATE_PATH.exists():
        client.create_bucket(bucket, acl=tos.ACLType.ACL_Private)

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=URL_TTL_SECONDS)
    persistent_objects = []
    resolved_assets = []
    for source in SOURCES:
        local = REPO_ROOT / source["local_path"]
        client.put_object_from_file(
            bucket,
            source["object_key"],
            str(local),
            content_type="image/png",
            forbid_overwrite=False,
        )
        head = client.head_object(bucket, source["object_key"])
        signed = client.pre_signed_url(
            tos.HttpMethodType.Http_Method_Get,
            bucket,
            source["object_key"],
            expires=URL_TTL_SECONDS,
        )
        size = local.stat().st_size
        persistent_objects.append(
            {
                "asset_id": source["asset_id"],
                "object_key": source["object_key"],
                "local_path": source["local_path"],
                "size_bytes": size,
                "sha256": sha256_file(local),
                "tos_etag": getattr(head, "etag", None),
            }
        )
        resolved_assets.append(
            {
                "asset_id": source["asset_id"],
                "local_path": source["local_path"],
                "remote_uri": signed.signed_url,
                "expires_at_utc": expires_at.isoformat(),
            }
        )

    write_json(
        STATE_PATH,
        {
            "provider": "Volcengine TOS",
            "region": REGION,
            "endpoint": ENDPOINT,
            "bucket": bucket,
            "acl": "private",
            "objects": persistent_objects,
        },
    )
    write_json(
        RUNTIME_PATH,
        {
            "bucket": bucket,
            "signed_url_ttl_seconds": URL_TTL_SECONDS,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "assets": resolved_assets,
        },
    )
    print(
        json.dumps(
            {
                "ok": True,
                "bucket": bucket,
                "region": REGION,
                "acl": "private",
                "uploaded": len(resolved_assets),
                "signed_url_ttl_hours": URL_TTL_SECONDS // 3600,
                "state_file": str(STATE_PATH),
                "runtime_file": str(RUNTIME_PATH),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

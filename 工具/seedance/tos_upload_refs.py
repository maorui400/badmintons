#!/usr/bin/env python3
"""Upload deduplicated assets for enabled episode shots and mint signed URLs."""

from __future__ import annotations

import hashlib
import argparse
import json
import mimetypes
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import tos


REPO_ROOT = Path(__file__).resolve().parents[2]
ENDPOINT = "tos-cn-beijing.volces.com"
REGION = "cn-beijing"
URL_TTL_SECONDS = 72 * 60 * 60


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def load_or_make_bucket_name(state_path: Path, episode_id: str) -> str:
    if state_path.exists():
        state = read_json(state_path)
        if state.get("bucket"):
            return str(state["bucket"])
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"badmintons-seedance-{episode_id.lower()}-{date_part}-{secrets.token_hex(4)}"


def collect_asset_entries(assets: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    entries.extend(assets.get("references") or [])
    for key in ("first_frame", "last_frame"):
        if assets.get(key):
            entries.append(assets[key])
    entries.extend(assets.get("action_videos") or [])
    entries.extend(assets.get("reference_audio") or [])
    return entries


def collect_enabled_sources(
    batch_path: Path,
    episode_dir: Path,
    episode_id: str,
) -> list[dict[str, str]]:
    batch = read_json(batch_path)
    by_local_path: dict[str, dict[str, str]] = {}
    for shot in batch.get("shots") or []:
        if not shot.get("enabled", True):
            continue
        shot_id = str(shot["shot_id"])
        assets_path = episode_dir / str(shot["assets_file"])
        assets = read_json(assets_path)
        for index, asset in enumerate(collect_asset_entries(assets), start=1):
            local_path = str(asset.get("local_path") or "").replace("\\", "/")
            if not local_path:
                continue
            local = REPO_ROOT / local_path
            if not local.is_file():
                raise FileNotFoundError(local)
            if local_path in by_local_path:
                continue
            digest = sha256_file(local)
            by_local_path[local_path] = {
                "asset_id": f"{shot_id}-REF-{index:02d}-{digest[:8]}",
                "local_path": local_path,
                "object_key": f"seedance/{episode_id}/shared/{digest[:16]}/{local.name}",
                "sha256": digest,
            }
    if not by_local_path:
        raise RuntimeError("No assets were found for enabled shots.")
    return list(by_local_path.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", default="EP01")
    args = parser.parse_args()
    episode_id = str(args.episode).strip().upper()
    if not episode_id or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in episode_id):
        raise ValueError("Invalid episode id.")
    episode_dir = REPO_ROOT / "制作" / episode_id
    batch_path = episode_dir / f"{episode_id}_批次清单.json"
    state_path = episode_dir / "tos_storage.json"
    runtime_path = episode_dir / "runtime" / "tos_assets.resolved.json"
    if not batch_path.is_file():
        raise FileNotFoundError(batch_path)

    ak = os.environ.get("TOS_ACCESS_KEY", "").strip()
    sk = os.environ.get("TOS_SECRET_KEY", "").strip()
    if not ak or not sk:
        raise RuntimeError("TOS credentials are not available in this process.")

    sources = collect_enabled_sources(batch_path, episode_dir, episode_id)
    client = tos.TosClientV2(ak, sk, ENDPOINT, REGION)
    bucket = load_or_make_bucket_name(state_path, episode_id)
    if not state_path.exists():
        client.create_bucket(bucket, acl=tos.ACLType.ACL_Private)

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=URL_TTL_SECONDS)
    persistent_objects = []
    resolved_assets = []
    for source in sources:
        local = REPO_ROOT / source["local_path"]
        content_type = mimetypes.guess_type(local.name)[0] or "application/octet-stream"
        client.put_object_from_file(
            bucket,
            source["object_key"],
            str(local),
            content_type=content_type,
            forbid_overwrite=False,
        )
        head = client.head_object(bucket, source["object_key"])
        signed = client.pre_signed_url(
            tos.HttpMethodType.Http_Method_Get,
            bucket,
            source["object_key"],
            expires=URL_TTL_SECONDS,
        )
        persistent_objects.append(
            {
                "asset_id": source["asset_id"],
                "object_key": source["object_key"],
                "local_path": source["local_path"],
                "size_bytes": local.stat().st_size,
                "sha256": source["sha256"],
                "content_type": content_type,
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
        state_path,
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
        runtime_path,
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
                "episode_id": episode_id,
                "state_file": str(state_path),
                "runtime_file": str(runtime_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

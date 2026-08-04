#!/usr/bin/env python3
"""Offline-first Seedance batch compiler and guarded API client."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APPROVAL_TOKEN = "API_CALL_CONFIRMED_FOR_THIS_RUN"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
VALID_STATUSES = {
    "PLANNED",
    "KEYFRAME-APPROVED",
    "PROMPT-READY",
    "API-APPROVED",
    "SUBMITTED",
    "GENERATED",
    "QC-PASS",
    "LOCKED",
}


class PipelineError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PipelineError(f"文件不存在：{path}") from exc
    except json.JSONDecodeError as exc:
        raise PipelineError(f"JSON 格式错误：{path}：{exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_from(base: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()


def rel_or_abs(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_batch(batch_path: Path) -> tuple[dict[str, Any], Path]:
    batch_path = batch_path.resolve()
    batch = read_json(batch_path)
    return batch, batch_path.parent


def validate_batch(batch_path: Path) -> dict[str, Any]:
    batch, batch_dir = load_batch(batch_path)
    runtime_remote_uris = load_runtime_remote_uris(batch_dir)
    errors: list[str] = []
    warnings: list[str] = []
    shots = batch.get("shots")
    if batch.get("pipeline_version") != "SEEDANCE-PIPELINE-v001":
        errors.append("pipeline_version 必须为 SEEDANCE-PIPELINE-v001")
    if not isinstance(shots, list) or not shots:
        errors.append("shots 必须是非空数组")
        shots = []

    ids: set[str] = set()
    dependency_map: dict[str, list[str]] = {}
    for index, shot in enumerate(shots):
        label = f"shots[{index}]"
        shot_id = shot.get("shot_id")
        if not shot_id:
            errors.append(f"{label} 缺少 shot_id")
            continue
        if shot_id in ids:
            errors.append(f"重复 shot_id：{shot_id}")
        ids.add(shot_id)
        dependency_map[shot_id] = list(shot.get("depends_on") or [])
        status = shot.get("status", "PLANNED")
        if status not in VALID_STATUSES:
            errors.append(f"{shot_id} 状态无效：{status}")

        for key in ("shot_file", "prompt_file", "assets_file"):
            value = shot.get(key)
            if not value:
                errors.append(f"{shot_id} 缺少 {key}")
                continue
            path = resolve_from(batch_dir, value)
            if not path.exists():
                errors.append(f"{shot_id} 的 {key} 不存在：{rel_or_abs(path)}")

        assets_value = shot.get("assets_file")
        if assets_value:
            assets_path = resolve_from(batch_dir, assets_value)
            if assets_path.exists():
                assets = read_json(assets_path)
                for asset in collect_assets(assets):
                    local = asset.get("local_path") or ""
                    remote = asset.get("remote_uri") or ""
                    if local:
                        local_path = resolve_from(REPO_ROOT, local)
                        if not local_path.exists():
                            errors.append(
                                f"{shot_id} 本地素材不存在：{rel_or_abs(local_path)}"
                            )
                    if local and not (remote or runtime_remote_uris.get(local)):
                        warnings.append(
                            f"{shot_id} 素材尚无远程 URI，当前只能离线编译：{local}"
                        )

    for shot_id, deps in dependency_map.items():
        for dep in deps:
            if dep not in ids:
                errors.append(f"{shot_id} 依赖不存在的镜头：{dep}")
        if shot_id in deps:
            errors.append(f"{shot_id} 不能依赖自身")

    return {
        "ok": not errors,
        "batch": rel_or_abs(batch_path.resolve()),
        "episode_id": batch.get("episode_id"),
        "shot_count": len(shots),
        "errors": errors,
        "warnings": warnings,
    }


def collect_assets(assets: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    result.extend(assets.get("references") or [])
    if assets.get("first_frame"):
        result.append(assets["first_frame"])
    if assets.get("last_frame"):
        result.append(assets["last_frame"])
    result.extend(assets.get("action_videos") or [])
    result.extend(assets.get("reference_audio") or [])
    return result


def load_runtime_remote_uris(batch_dir: Path) -> dict[str, str]:
    runtime_path = batch_dir / "runtime" / "tos_assets.resolved.json"
    if not runtime_path.exists():
        return {}
    runtime = read_json(runtime_path)
    resolved: dict[str, str] = {}
    now = datetime.now(timezone.utc)
    for asset in runtime.get("assets") or []:
        local_path = asset.get("local_path") or ""
        remote_uri = asset.get("remote_uri") or ""
        expires_at = asset.get("expires_at_utc")
        if not local_path or not remote_uri or not expires_at:
            continue
        try:
            expiry = datetime.fromisoformat(expires_at)
        except ValueError:
            continue
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry > now:
            resolved[local_path] = remote_uri
    return resolved


def directive_prompt(prompt: str, shot_cfg: dict[str, Any]) -> str:
    ratio = shot_cfg.get("ratio", "16:9")
    duration = int(shot_cfg.get("duration", 5))
    resolution = shot_cfg.get("resolution", "720p")
    generate_audio = str(bool(shot_cfg.get("generate_audio", False))).lower()
    return (
        f"{prompt.strip()}\n\n"
        f"--ratio {ratio} --dur {duration} --resolution {resolution} "
        f"--generate_audio {generate_audio}"
    )


def compile_shot(
    batch: dict[str, Any],
    batch_dir: Path,
    shot: dict[str, Any],
) -> dict[str, Any]:
    shot_id = shot["shot_id"]
    shot_cfg = read_json(resolve_from(batch_dir, shot["shot_file"]))
    assets = read_json(resolve_from(batch_dir, shot["assets_file"]))
    runtime_remote_uris = load_runtime_remote_uris(batch_dir)
    prompt_path = resolve_from(batch_dir, shot["prompt_file"])
    prompt = directive_prompt(prompt_path.read_text(encoding="utf-8"), shot_cfg)
    defaults = batch.get("defaults") or {}
    model = shot_cfg.get("model") or defaults.get("model")

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    unresolved: list[dict[str, str]] = []
    for asset in collect_assets(assets):
        local = asset.get("local_path") or ""
        remote = asset.get("remote_uri") or runtime_remote_uris.get(local, "")
        label = asset.get("label") or "未命名素材"
        media_type = asset.get("type") or infer_media_type(local or remote)
        if not remote:
            unresolved.append({"label": label, "local_path": local})
            remote = f"__REMOTE_URI_REQUIRED__:{local}"
        item: dict[str, Any] = {
            "type": media_type,
            media_type: {"url": remote},
        }
        role = asset.get("role")
        if role:
            item["role"] = role
        content.append(item)

    payload: dict[str, Any] = {
        "model": model,
        "content": content,
        "return_last_frame": bool(
            shot_cfg.get(
                "return_last_frame",
                defaults.get("return_last_frame", True),
            )
        ),
    }
    callback = (batch.get("api") or {}).get("callback_url")
    if callback:
        payload["callback_url"] = callback

    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return {
        "shot_id": shot_id,
        "status": shot.get("status"),
        "depends_on": shot.get("depends_on") or [],
        "continuity_from": shot.get("continuity_from"),
        "payload_sha256": hashlib.sha256(canonical).hexdigest(),
        "network_ready": not unresolved,
        "unresolved_assets": unresolved,
        "request": payload,
    }


def infer_media_type(value: str) -> str:
    suffix = Path(value.split("?")[0]).suffix.lower()
    if suffix in {".mp4", ".mov", ".webm"}:
        return "video_url"
    if suffix in {".mp3", ".wav", ".m4a", ".aac"}:
        return "audio_url"
    return "image_url"


def compile_batch(batch_path: Path) -> dict[str, Any]:
    report = validate_batch(batch_path)
    if report["errors"]:
        raise PipelineError("批次验证失败，请先修复 errors")
    batch, batch_dir = load_batch(batch_path)
    build_dir = batch_dir / "_build"
    requests_dir = build_dir / "requests"
    compiled: list[dict[str, Any]] = []
    for shot in batch["shots"]:
        if not shot.get("enabled", True):
            continue
        item = compile_shot(batch, batch_dir, shot)
        compiled.append(item)
        write_json(requests_dir / f"{item['shot_id']}.request.preview.json", item)
    manifest = {
        "pipeline_version": batch["pipeline_version"],
        "episode_id": batch.get("episode_id"),
        "compiled_at_unix": int(time.time()),
        "network_used": False,
        "shots": compiled,
    }
    write_json(build_dir / "compiled_manifest.json", manifest)
    return {
        "ok": True,
        "network_used": False,
        "compiled_shots": len(compiled),
        "network_ready_shots": sum(1 for item in compiled if item["network_ready"]),
        "unresolved_shots": [
            item["shot_id"] for item in compiled if not item["network_ready"]
        ],
        "output": rel_or_abs(build_dir / "compiled_manifest.json"),
    }


def require_api_approval(value: str | None) -> str:
    if value != APPROVAL_TOKEN:
        raise PipelineError(
            "联网动作被拒绝：必须在用户确认本轮 API 操作后，显式传入 "
            f"--approve-api-call {APPROVAL_TOKEN}"
        )
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        raise PipelineError("未设置环境变量 ARK_API_KEY")
    return api_key


def api_request(
    method: str,
    url: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise PipelineError(f"API HTTP {exc.code}：{body}") from exc
    except urllib.error.URLError as exc:
        raise PipelineError(f"API 网络错误：{exc}") from exc


def submit_batch(batch_path: Path, approval: str | None) -> dict[str, Any]:
    api_key = require_api_approval(approval)
    compile_batch(batch_path)
    batch, batch_dir = load_batch(batch_path)
    manifest_path = batch_dir / "_build" / "compiled_manifest.json"
    manifest = read_json(manifest_path)
    unresolved = [
        item["shot_id"] for item in manifest["shots"] if not item["network_ready"]
    ]
    if unresolved:
        raise PipelineError(f"以下镜头仍有未上传素材，拒绝提交：{', '.join(unresolved)}")

    state_path = batch_dir / "_build" / "state" / "registry.json"
    state = read_json(state_path) if state_path.exists() else {"tasks": {}}
    base_url = ((batch.get("api") or {}).get("base_url") or DEFAULT_BASE_URL).rstrip("/")
    submitted: list[dict[str, str]] = []
    skipped: list[str] = []
    for item in manifest["shots"]:
        shot_id = item["shot_id"]
        old = state["tasks"].get(shot_id)
        if old and old.get("payload_sha256") == item["payload_sha256"]:
            skipped.append(shot_id)
            continue
        if item.get("depends_on"):
            incomplete = [
                dep
                for dep in item["depends_on"]
                if state["tasks"].get(dep, {}).get("status") != "succeeded"
            ]
            if incomplete:
                skipped.append(shot_id)
                continue
        result = api_request(
            "POST",
            f"{base_url}/contents/generations/tasks",
            api_key,
            item["request"],
        )
        task_id = result.get("id")
        if not task_id:
            raise PipelineError(f"{shot_id} 未返回任务 ID：{result}")
        state["tasks"][shot_id] = {
            "task_id": task_id,
            "payload_sha256": item["payload_sha256"],
            "status": "submitted",
            "submitted_at_unix": int(time.time()),
        }
        write_json(state_path, state)
        submitted.append({"shot_id": shot_id, "task_id": task_id})
    return {"submitted": submitted, "skipped": skipped, "registry": rel_or_abs(state_path)}


def query_status(batch_path: Path, approval: str | None) -> dict[str, Any]:
    api_key = require_api_approval(approval)
    batch, batch_dir = load_batch(batch_path)
    state_path = batch_dir / "_build" / "state" / "registry.json"
    if not state_path.exists():
        raise PipelineError("没有已提交任务记录")
    state = read_json(state_path)
    base_url = ((batch.get("api") or {}).get("base_url") or DEFAULT_BASE_URL).rstrip("/")
    results: dict[str, Any] = {}
    for shot_id, task in state.get("tasks", {}).items():
        result = api_request(
            "GET",
            f"{base_url}/contents/generations/tasks/{task['task_id']}",
            api_key,
        )
        task["status"] = result.get("status", "unknown")
        task["last_result"] = result
        results[shot_id] = {
            "task_id": task["task_id"],
            "status": task["status"],
        }
    write_json(state_path, state)
    return results


def download_results(batch_path: Path, approval: str | None) -> dict[str, Any]:
    api_key = require_api_approval(approval)
    del api_key
    batch, batch_dir = load_batch(batch_path)
    enabled_shot_ids = {
        shot["shot_id"] for shot in batch.get("shots", []) if shot.get("enabled", True)
    }
    state_path = batch_dir / "_build" / "state" / "registry.json"
    if not state_path.exists():
        raise PipelineError("没有任务状态记录")
    state = read_json(state_path)
    output_dir = batch_dir / "_build" / "outputs"
    downloaded: list[str] = []
    for shot_id, task in state.get("tasks", {}).items():
        if shot_id not in enabled_shot_ids:
            continue
        result = task.get("last_result") or {}
        if result.get("status") != "succeeded":
            continue
        content = result.get("content") or {}
        url = content.get("video_url")
        if not url:
            continue
        target = output_dir / f"{shot_id}.mp4"
        target.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, target)
        downloaded.append(rel_or_abs(target))
    return {"downloaded": downloaded}


def doctor() -> dict[str, Any]:
    ffmpeg = find_ffmpeg()
    return {
        "repo_root": str(REPO_ROOT),
        "python": sys.version.split()[0],
        "ark_api_key_configured": bool(os.environ.get("ARK_API_KEY")),
        "ffmpeg_available": bool(ffmpeg),
        "ffmpeg_path": str(ffmpeg) if ffmpeg else None,
        "network_default": "DENY",
        "approval_token_required": True,
    }


def find_ffmpeg() -> Path | None:
    configured = os.environ.get("FFMPEG_BIN")
    if configured:
        candidate = Path(configured)
        if candidate.is_dir():
            candidate = candidate / "ffmpeg.exe"
        if candidate.exists():
            return candidate
    system = shutil.which("ffmpeg")
    if system:
        return Path(system)
    winget_root = (
        Path.home()
        / "AppData"
        / "Local"
        / "Microsoft"
        / "WinGet"
        / "Packages"
    )
    if winget_root.exists():
        candidates = sorted(
            winget_root.glob("Gyan.FFmpeg*/ffmpeg-*/bin/ffmpeg.exe"),
            reverse=True,
        )
        if candidates:
            return candidates[0]
    return None


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    for name in ("validate", "compile", "submit", "status", "download"):
        command = sub.add_parser(name)
        command.add_argument("batch", type=Path)
        if name in {"submit", "status", "download"}:
            command.add_argument("--approve-api-call")
    return parser


def main() -> int:
    args = make_parser().parse_args()
    try:
        if args.command == "doctor":
            result = doctor()
        elif args.command == "validate":
            result = validate_batch(args.batch)
        elif args.command == "compile":
            result = compile_batch(args.batch)
        elif args.command == "submit":
            result = submit_batch(args.batch, args.approve_api_call)
        elif args.command == "status":
            result = query_status(args.batch, args.approve_api_call)
        else:
            result = download_results(args.batch, args.approve_api_call)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 2
    except PipelineError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

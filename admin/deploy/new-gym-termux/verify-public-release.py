#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import hashlib
import json
import re


GRAVITY_MARKERS = (
    "gravityfitnessnmh",
    "gravity-authe",
    "917999526112",
    "foyer-amenity-staff.ngrok-free.dev",
)


def verify_release(path: Path, *, expected_release_id: str | None = None) -> dict[str, object]:
    release = path.resolve()
    index = release / "index.html"
    config = release / "js" / "gym-config.js"
    manifest_path = release / ".new-gym-release.json"
    if not release.is_dir():
        raise ValueError("Release directory does not exist")
    if not index.is_file():
        raise ValueError("Release is missing index.html")
    if not config.is_file():
        raise ValueError("Release is missing gym-config.js")
    if not manifest_path.is_file():
        raise ValueError("Release is missing manifest")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Release manifest is not valid JSON") from error

    release_id = str(manifest.get("releaseId") or "")
    if expected_release_id is not None and release_id != expected_release_id:
        raise ValueError("Manifest release id mismatch")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", release_id) or ".." in release_id:
        raise ValueError("Invalid release id in manifest")

    expected_sha = str(manifest.get("customerConfigSha256") or "").lower()
    actual_sha = hashlib.sha256(config.read_bytes()).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha) or expected_sha != actual_sha:
        raise ValueError("Customer config hash mismatch")

    commit = str(manifest.get("gitCommit") or "")
    if commit != "nogit" and not re.fullmatch(r"[0-9a-f]{7,40}", commit):
        raise ValueError("Invalid Git commit in manifest")

    config_text = config.read_text(encoding="utf-8").casefold()
    if any(marker in config_text for marker in GRAVITY_MARKERS):
        raise ValueError("Release contains Gravity live values")

    return {
        "ready": True,
        "releaseId": release_id,
        "gitCommit": commit,
        "customerConfigSha256": actual_sha,
        "complete": bool(manifest.get("complete")),
    }


def main() -> int:
    parser = ArgumentParser(description="Verify a generated New Gym public release.")
    parser.add_argument("--release", required=True)
    parser.add_argument("--release-id")
    args = parser.parse_args()

    try:
        result = verify_release(
            Path(args.release).expanduser(),
            expected_release_id=args.release_id,
        )
    except ValueError as error:
        print(json.dumps({"ready": False, "error": str(error)}, separators=(",", ":"), sort_keys=True))
        return 2
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

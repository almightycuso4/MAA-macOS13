#!/usr/bin/env python3
"""Read the pinned MAA release manifest used by the macOS 13 build."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "release-manifest.json"


def load_manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("Release manifest must be a JSON object")
    default_tag = data.get("default_tag")
    if not isinstance(default_tag, str) or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", default_tag):
        raise SystemExit("Release manifest has an invalid default_tag")
    releases = data.get("releases")
    if not isinstance(releases, dict):
        raise SystemExit("Release manifest has no releases mapping")
    return data


def asset_for(tag: str) -> tuple[str, str, str]:
    data = load_manifest()
    release = data["releases"].get(tag)
    if not isinstance(release, dict):
        raise SystemExit(
            f"No pinned macOS DMG/checksum for {tag}. Add the official asset name and SHA-256 to {MANIFEST}."
        )
    filename = release.get("macos_dmg")
    digest = release.get("macos_dmg_sha256")
    repository = data.get("release_repository")
    if not isinstance(filename, str) or not re.fullmatch(r"MAA-v[0-9]+\.[0-9]+\.[0-9]+-macos-universal\.dmg", filename):
        raise SystemExit(f"Invalid macOS DMG filename for {tag}")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise SystemExit(f"Invalid SHA-256 for {tag}")
    if filename != f"MAA-{tag}-macos-universal.dmg":
        raise SystemExit(f"DMG filename/tag mismatch for {tag}: {filename}")
    if repository != "MaaAssistantArknights/MaaRelease":
        raise SystemExit(f"Unexpected release asset repository: {repository}")
    return filename, digest, repository


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--default":
        print(load_manifest()["default_tag"])
        return 0
    if len(sys.argv) == 2:
        filename, digest, repository = asset_for(sys.argv[1])
        print(f"{filename}\t{digest}\t{repository}")
        return 0
    print("Usage: release_manifest.py --default | RELEASE_TAG", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

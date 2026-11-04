#!/usr/bin/env python3
"""Download only matching-tag MaaCore include/ files with GitHub Contents API.

The full MAA source archive is over 100 MB; the build only consumes include/.
This authenticated, path-scoped download avoids the large archive dependency.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

REPOSITORY = "MaaAssistantArknights/MaaAssistantArknights"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}/contents"
TAG_FORMAT = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+(?:[.-][A-Za-z0-9.-]+)?\Z")
MAX_FILES = 500
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 40 * 1024 * 1024
RETRIES = 5


class HeaderDownloadError(Exception):
    pass


def request_json(path: str, tag: str, token: str) -> object:
    url = API_ROOT + "/" + quote(path, safe="/") + "?ref=" + quote(tag, safe="")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "MAA-macOS13-build-header-fetch",
    }
    if token:
        headers["Authorization"] = "Bearer " + token

    for attempt in range(RETRIES):
        try:
            with urlopen(Request(url, headers=headers), timeout=45) as response:
                return json.load(response)
        except HTTPError as exc:
            # A bad tag, permission error or exhausted rate limit is not fixed
            # by re-requesting the same URL in a loop.
            retry = exc.code in (408, 429, 500, 502, 503, 504)
            detail = f"GitHub API HTTP {exc.code} for {path} (tag {tag})"
            if not retry or attempt == RETRIES - 1:
                raise HeaderDownloadError(detail) from exc
        except (URLError, TimeoutError, ConnectionError, OSError, ValueError) as exc:
            detail = f"GitHub API error for {path}: {type(exc).__name__}: {exc}"
            if attempt == RETRIES - 1:
                raise HeaderDownloadError(detail) from exc
        wait = min(2 ** attempt, 12)
        print(f"Core headers: transient fetch failure; retry {attempt + 2}/{RETRIES} in {wait}s", flush=True)
        time.sleep(wait)
    raise AssertionError("unreachable")


def safe_relative(path: str) -> Path:
    posix = PurePosixPath(path)
    if not path.startswith("include/") or any(part in ("", ".", "..") for part in path.split("/")):
        raise HeaderDownloadError(f"Unsafe or out-of-scope path in GitHub response: {path!r}")
    return Path(*posix.parts[1:])


def download(tag: str, destination: Path, token: str) -> list[tuple[str, int]]:
    if not TAG_FORMAT.fullmatch(tag):
        raise HeaderDownloadError(f"Invalid MAA release tag: {tag!r}")
    downloaded: list[tuple[str, int]] = []
    pending = ["include"]
    visited = set()
    total = 0
    while pending:
        directory = pending.pop()
        if directory in visited:
            raise HeaderDownloadError(f"Repeated directory {directory}")
        visited.add(directory)
        listing = request_json(directory, tag, token)
        if not isinstance(listing, list):
            raise HeaderDownloadError(f"Expected directory listing at {directory}")
        for entry in listing:
            if not isinstance(entry, dict):
                raise HeaderDownloadError(f"Invalid listing entry in {directory}")
            path = entry.get("path")
            typ = entry.get("type")
            if not isinstance(path, str):
                raise HeaderDownloadError(f"Invalid listing path in {directory}")
            rel = safe_relative(path)
            if typ == "dir":
                pending.append(path)
            elif typ == "file":
                if len(downloaded) >= MAX_FILES:
                    raise HeaderDownloadError("Too many include/ files")
                size = entry.get("size")
                if not isinstance(size, int) or size < 0 or size > MAX_FILE_BYTES:
                    raise HeaderDownloadError(f"Unexpected file size at {path}: {size}")
                item = request_json(path, tag, token)
                if not isinstance(item, dict) or item.get("type") != "file":
                    raise HeaderDownloadError(f"Invalid file response for {path}")
                if item.get("encoding") != "base64" or not isinstance(item.get("content"), str):
                    raise HeaderDownloadError(f"Expected base64 content for {path}")
                try:
                    content = base64.b64decode(item["content"], validate=False)
                except (ValueError, binascii.Error) as exc:
                    raise HeaderDownloadError(f"Bad base64 data at {path}") from exc
                if len(content) != size:
                    raise HeaderDownloadError(f"File size mismatch for {path}: got {len(content)}, expected {size}")
                total += len(content)
                if total > MAX_TOTAL_BYTES:
                    raise HeaderDownloadError("include/ content exceeds safety limit")
                blob_sha = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
                if blob_sha != entry.get("sha") or blob_sha != item.get("sha"):
                    raise HeaderDownloadError(f"Git blob SHA mismatch for {path}")
                target = destination / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                downloaded.append((path, len(content)))
                print(f"Core headers: verified {path} ({len(content)} bytes)", flush=True)
            else:
                raise HeaderDownloadError(f"Unsupported include/ entry {path}: {typ}")
    if not (destination / "AsstCaller.h").is_file():
        raise HeaderDownloadError("The matching release has no include/AsstCaller.h")
    if not (destination / "AsstCallerExtra.h").is_file():
        raise HeaderDownloadError("The matching release has no include/AsstCallerExtra.h")
    return downloaded


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: fetch_core_headers.py RELEASE_TAG HEADERS_DIR LOG_DIR", file=sys.stderr)
        return 2
    tag, output_dir, log_dir = sys.argv[1:]
    output = Path(output_dir)
    logs = Path(log_dir)
    logs.mkdir(parents=True, exist_ok=True)
    log_file = logs / "core-header-download.txt"
    log_file.write_text(f"Official repository: {REPOSITORY}\nRelease tag: {tag}\nMethod: GitHub Contents API\n")
    try:
        files = download(tag, output, os.environ.get("GH_TOKEN", ""))
    except HeaderDownloadError as exc:
        with log_file.open("a") as out:
            out.write(f"FAILED: {exc}\n")
        print(f"Core header download FAILED: {exc}", file=sys.stderr)
        return 1
    with log_file.open("a") as out:
        out.write(f"Verified file count: {len(files)}\nVerified byte count: {sum(size for _,size in files)}\n")
        for name, size in sorted(files):
            out.write(f"{name} ({size} bytes): verified Git blob SHA-1\n")
        out.write("Result: PASS\n")
    print(f"Core header download PASS: {len(files)} files, {sum(n for _,n in files)} bytes, tag {tag}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

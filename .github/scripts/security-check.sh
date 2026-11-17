#!/usr/bin/env bash
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"

python3 - <<'PY'
import os
import pathlib
import subprocess
import sys

root = pathlib.Path.cwd()
tracked = subprocess.run(
    ["git", "ls-files", "-z"], check=True, stdout=subprocess.PIPE
).stdout.split(b"\0")
tracked_paths = [pathlib.Path(os.fsdecode(item)) for item in tracked if item]
sensitive = [
    path.as_posix()
    for path in tracked_paths
    if path.name.startswith(".env") and path.name != ".env.example"
]
if sensitive:
    print("Security check failed: sensitive .env file(s) are tracked:")
    print("\n".join(sensitive))
    raise SystemExit(1)

prefix = b"-----BEGIN "
suffix = b" KEY-----"
markers = tuple(prefix + kind + suffix for kind in (
    b"PRIVATE", b"RSA PRIVATE", b"EC PRIVATE", b"OPENSSH PRIVATE", b"DSA PRIVATE",
    b"ENCRYPTED PRIVATE",
))
excluded = {".codex", ".venv", "venv", "node_modules", ".next", "__pycache__"}
hits = []
for relative in tracked_paths:
    if any(part in excluded for part in relative.parts):
        continue
    path = root / relative
    try:
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        data = path.read_bytes()
    except OSError:
        continue
    if any(marker in data for marker in markers):
        hits.append(relative.as_posix())
if hits:
    print("Security check failed: private-key marker(s) found:")
    print("\n".join(hits))
    raise SystemExit(1)
print("Security check passed: no tracked .env secrets or private-key markers found")
PY

#!/usr/bin/env bash
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"

run_python() {
  if python3 -c 'import tomllib' >/dev/null 2>&1; then
    python3 "$@"
  else
    uv run --project backend python "$@"
  fi
}

run_python - <<'PY'
import json
import pathlib
import re
import tomllib

root = pathlib.Path.cwd()
required = (
    "backend/pyproject.toml",
    "backend/uv.lock",
    "frontend/package.json",
    "frontend/package-lock.json",
    "compose.yaml",
    "Dockerfile",
    "frontend/Dockerfile",
)
missing = [path for path in required if not (root / path).is_file()]
if missing:
    raise SystemExit(f"Preflight failed: missing manifests/lockfiles: {', '.join(missing)}")

project = tomllib.loads((root / "backend/pyproject.toml").read_text())
python_dependencies = project.get("project", {}).get("dependencies", [])
if not python_dependencies or any(not re.search(r"==[^=]+$", item) for item in python_dependencies):
    raise SystemExit("Preflight failed: Python runtime dependencies must be exactly pinned")

manifest = json.loads((root / "frontend/package.json").read_text())
lock = json.loads((root / "frontend/package-lock.json").read_text())
if lock.get("lockfileVersion") not in (2, 3):
    raise SystemExit("Preflight failed: unsupported or missing npm lockfile version")
if manifest.get("version") != lock.get("version"):
    raise SystemExit("Preflight failed: package.json and package-lock.json versions differ")
locked_root = lock.get("packages", {}).get("")
if not isinstance(locked_root, dict):
    raise SystemExit("Preflight failed: npm lockfile has no root package metadata")
if manifest.get("name") != locked_root.get("name") or manifest.get("version") != locked_root.get("version"):
    raise SystemExit("Preflight failed: npm lockfile root metadata differs from package.json")
for section in ("dependencies", "devDependencies", "optionalDependencies"):
    expected = manifest.get(section, {})
    actual = locked_root.get(section, {})
    if expected != actual:
        raise SystemExit(f"Preflight failed: package.json and package-lock.json differ in {section}")
    if any(not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", value) for value in expected.values()):
        raise SystemExit(f"Preflight failed: frontend {section} must use exact versions")
print("Preflight passed: required manifests and lockfiles are present and consistent")
PY

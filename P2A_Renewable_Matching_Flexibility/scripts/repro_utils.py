from __future__ import annotations
from pathlib import Path
import hashlib, json, shutil, subprocess, sys
from datetime import datetime, timezone


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def file_hashes(paths, base: Path | None = None):
    out = {}
    for p in paths:
        p = Path(p)
        if not p.is_file():
            continue
        key = str(p)
        if base is not None:
            try:
                key = str(p.resolve().relative_to(Path(base).resolve()))
            except ValueError:
                key = p.name
        out[key] = sha256(p)
    return out


def tee_command(cmd, cwd: Path, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('w', encoding='utf-8', newline='') as log:
        proc = subprocess.Popen(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, bufsize=1)
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end='', flush=True)
            log.write(line)
        return proc.wait()


def require_executable(name: str):
    if shutil.which(name) is None:
        raise SystemExit(f"Required executable not found on PATH: {name}")


def write_manifest(path: Path, payload: dict):
    payload = dict(payload)
    payload['created_utc'] = datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')

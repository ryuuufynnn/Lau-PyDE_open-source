from pathlib import Path

import json
import hashlib
import time

def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")

def write_file(path: str, content: str) -> str:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    # file_path.write_text("print('PyDE is an open source lightweight Python IDE.')")


def _recovery_dir() -> Path:
    path = Path.home() / ".lau_pyde_recovery"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_recovery(original_path: str | None, content: str) -> str:
    key_source = (original_path or "<unsaved>") + "::" + str(time.time())
    key = hashlib.sha1(key_source.encode("utf-8")).hexdigest()
    d = _recovery_dir()
    content_path = d / f"{key}.py"
    meta_path = d / f"{key}.json"
    content_path.write_text(content or "", encoding="utf-8")
    meta = {
        "key": key,
        "original_path": original_path,
        "timestamp": time.time(),
        "content_file": str(content_path),
    }
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    return key


def list_recoveries() -> list[dict]:
    d = _recovery_dir()
    items: list[dict] = []
    for p in d.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            items.append(data)
        except Exception:
            continue
    items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return items


def read_recovery(key: str) -> tuple[str | None, str]:
    d = _recovery_dir()
    meta_path = d / f"{key}.json"
    if not meta_path.exists():
        return None, ""
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        content_file = meta.get("content_file")
        content = Path(content_file).read_text(encoding="utf-8") if content_file and Path(content_file).exists() else ""
        return meta.get("original_path"), content
    except Exception:
        return None, ""


def remove_recovery(key: str) -> None:
    d = _recovery_dir()
    for suffix in (".json", ".py"):
        p = d / f"{key}{suffix}"
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass


def remove_recovery_for_path(original_path: str) -> None:
    for meta in list_recoveries():
        if meta.get("original_path") == original_path:
            try:
                remove_recovery(meta.get("key"))
            except Exception:
                pass
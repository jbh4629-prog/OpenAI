#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import re
import shutil

CONFIG_ROOT = Path.home() / ".config"
BACKUP_ROOT = Path.home() / ".codespace-cleanup-backups" / datetime.now().strftime("%Y%m%d_%H%M%S")

PATH_PATTERNS = [
    re.compile(r"ouroboros", re.IGNORECASE),
    re.compile(r"modelcontextprotocol", re.IGNORECASE),
]

CONTENT_PATTERNS = [
    re.compile(r"ouroboros", re.IGNORECASE),
    re.compile(r"modelcontextprotocol", re.IGNORECASE),
    re.compile(r"claude\s+plugin", re.IGNORECASE),
]

TEXT_SUFFIXES = {
    ".json",
    ".jsonc",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".md",
    ".conf",
}

JSON_FILENAMES = {
    ".mcp.json",
    "mcp.json",
    "settings.json",
    "config.json",
}


def matches_any_pattern(value: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(pattern.search(value) for pattern in patterns)


def backup_path(path: Path) -> Path:
    return BACKUP_ROOT / path.relative_to(Path.home())


def backup_file(path: Path) -> None:
    target = backup_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def backup_dir(path: Path) -> None:
    target = backup_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(path, target, dirs_exist_ok=True)


def path_is_suspicious(path: Path) -> bool:
    return matches_any_pattern(str(path), PATH_PATTERNS)


def text_file_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in JSON_FILENAMES


def text_contains_suspicious_content(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return matches_any_pattern(text, CONTENT_PATTERNS)


def scrub_json(obj):
    changed = False

    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            if matches_any_pattern(str(key), CONTENT_PATTERNS):
                changed = True
                continue
            new_value, child_changed = scrub_json(value)
            if isinstance(new_value, str) and matches_any_pattern(new_value, CONTENT_PATTERNS):
                changed = True
                continue
            new_obj[key] = new_value
            changed = changed or child_changed
        return new_obj, changed

    if isinstance(obj, list):
        new_list = []
        for item in obj:
            new_item, child_changed = scrub_json(item)
            if isinstance(new_item, str) and matches_any_pattern(new_item, CONTENT_PATTERNS):
                changed = True
                continue
            new_list.append(new_item)
            changed = changed or child_changed
        return new_list, changed

    return obj, False


def clean_json_file(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False

    cleaned, changed = scrub_json(data)
    if not changed:
        return False

    backup_file(path)
    path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def clean_text_file(path: Path) -> bool:
    try:
        original = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    lines = original.splitlines()
    cleaned_lines = []
    changed = False

    for line in lines:
        if matches_any_pattern(line, CONTENT_PATTERNS):
            changed = True
            continue
        cleaned_lines.append(line)

    if not changed:
        return False

    backup_file(path)
    path.write_text("\n".join(cleaned_lines).rstrip() + "\n", encoding="utf-8")
    return True


def main() -> int:
    print("[cleanup-user-config] scanning ~/.config for ouroboros and MCP traces")

    if not CONFIG_ROOT.exists():
        print("[cleanup-user-config] ~/.config not found; nothing to clean")
        return 0

    removed_paths: set[Path] = set()
    cleaned_files: list[Path] = []

    for path in sorted(CONFIG_ROOT.rglob("*"), key=lambda item: len(item.parts)):
        if any(parent in removed_paths for parent in path.parents):
            continue

        if not path_is_suspicious(path):
            continue

        if path.is_dir():
            backup_dir(path)
            shutil.rmtree(path)
            removed_paths.add(path)
            print(f"[cleanup-user-config] removed directory: {path}")
        elif path.is_file():
            backup_file(path)
            path.unlink(missing_ok=True)
            removed_paths.add(path)
            print(f"[cleanup-user-config] removed file: {path}")

    for path in sorted(CONFIG_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(parent in removed_paths for parent in path.parents):
            continue
        if not text_file_candidate(path):
            continue
        if not text_contains_suspicious_content(path):
            continue

        cleaned = False
        if path.suffix.lower() == ".json" or path.name in JSON_FILENAMES:
            cleaned = clean_json_file(path)
        if not cleaned:
            cleaned = clean_text_file(path)
        if cleaned:
            cleaned_files.append(path)
            print(f"[cleanup-user-config] cleaned file: {path}")

    if removed_paths or cleaned_files:
        print(f"[cleanup-user-config] backup written under: {BACKUP_ROOT}")
    else:
        print("[cleanup-user-config] no matching traces found under ~/.config")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

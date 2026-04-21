from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import json


class SessionStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(".ouroboros")
        self.root.mkdir(parents=True, exist_ok=True)
        self.sessions_root = self.root / "sessions"
        self.sessions_root.mkdir(parents=True, exist_ok=True)

    def session_dir(self, session_id: str) -> Path:
        path = self.sessions_root / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_json(self, session_id: str, name: str, payload: Any) -> Path:
        path = self.session_dir(session_id) / name
        serializable = asdict(payload) if hasattr(payload, "__dataclass_fields__") else payload
        path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def read_json(self, session_id: str, name: str) -> dict[str, Any]:
        return json.loads((self.session_dir(session_id) / name).read_text(encoding="utf-8"))

    def write_text(self, session_id: str, name: str, content: str) -> Path:
        path = self.session_dir(session_id) / name
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        return path

    def list_session_files(self, session_id: str) -> list[Path]:
        return sorted(self.session_dir(session_id).glob("*"))

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import shlex
import subprocess
import tempfile
from typing import Any


class CodexBackendError(RuntimeError):
    pass


@dataclass(slots=True)
class CodexResult:
    stdout: str
    stderr: str
    command: list[str]
    returncode: int


class CodexBackend:
    """Thin subprocess wrapper around Codex CLI."""

    def __init__(
        self,
        executable: str | None = None,
        command_template: str | None = None,
        cwd: str | None = None,
        timeout_seconds: int = 600,
    ) -> None:
        self.executable = executable or os.environ.get("OURO_CODEX_EXECUTABLE", "codex")
        self.command_template = command_template or os.environ.get("OURO_CODEX_COMMAND_TEMPLATE")
        self.cwd = cwd or os.getcwd()
        self.timeout_seconds = timeout_seconds

    def _build_command(self, prompt: str) -> list[str]:
        if self.command_template:
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as handle:
                handle.write(prompt)
                prompt_file = handle.name
            rendered = self.command_template.format(
                prompt=prompt,
                prompt_file=prompt_file,
                cwd=self.cwd,
            )
            return shlex.split(rendered)
        return [self.executable, "exec", prompt]

    def run(self, prompt: str) -> CodexResult:
        command = self._build_command(prompt)
        try:
            completed = subprocess.run(
                command,
                cwd=self.cwd,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CodexBackendError(
                f"Codex CLI executable not found: {command[0]}. Install @openai/codex or set OURO_CODEX_EXECUTABLE/OURO_CODEX_COMMAND_TEMPLATE."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise CodexBackendError(
                f"Codex CLI timed out after {self.timeout_seconds} seconds."
            ) from exc
        if completed.returncode != 0:
            raise CodexBackendError(
                "Codex CLI returned a non-zero exit code.\n"
                f"Command: {' '.join(command)}\n"
                f"STDERR:\n{completed.stderr.strip()}"
            )
        return CodexResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            command=command,
            returncode=completed.returncode,
        )


def extract_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if not text:
        raise CodexBackendError("Codex CLI returned empty output.")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise CodexBackendError("Could not locate JSON object in Codex output.")
    return json.loads(text[start : end + 1])

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def run(*cmd: str) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    if args.clean:
        shutil.rmtree(ROOT / "build", ignore_errors=True)
        shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir(exist_ok=True)

    arch = platform.machine().lower().replace("amd64", "x64").replace("x86_64", "x64").replace("aarch64", "arm64")
    system = {"Darwin": "macos", "Windows": "windows", "Linux": "linux"}[platform.system()]
    binary_name = "insane-search-mcp.exe" if system == "windows" else "insane-search-mcp"
    data_sep = os.pathsep
    engine_root = ROOT / "skills" / "insane-search" / "engine"

    run(
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onedir", "--clean",
        "--name", "insane-search-mcp",
        "--paths", str(ROOT / "skills" / "insane-search"),
        "--add-data", f"{engine_root / 'waf_profiles.yaml'}{data_sep}engine",
        "--add-data", f"{engine_root / 'templates'}{data_sep}engine/templates",
        "--collect-all", "curl_cffi",
        "--collect-all", "bs4",
        "--collect-all", "markdownify",
        "--collect-all", "yaml",
        "--collect-all", "pdfplumber",
        "--collect-submodules", "engine",
        "--hidden-import", "engine",
        "--hidden-import", "engine.fetch_chain",
        "--hidden-import", "engine.phase0",
        "--hidden-import", "engine.x_search",
        "--hidden-import", "engine.x_search_io",
        "--hidden-import", "yt_dlp",
        str(ROOT / "backend" / "__main__.py"),
    )

    bundle = DIST / f"insane-search-{system}-{arch}"
    shutil.rmtree(bundle, ignore_errors=True)
    bundle.mkdir(parents=True)
    shutil.copytree(DIST / "insane-search-mcp", bundle / "runtime")
    shutil.copytree(ROOT / "skills" / "insane-search", bundle / "skill" / "insane-search", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "observations"))
    shutil.copy2(ROOT / ".codex-plugin" / "plugin.json", bundle / "plugin.json")
    if (ROOT / "LICENSE").exists():
        shutil.copy2(ROOT / "LICENSE", bundle / "LICENSE")
    if system == "windows":
        shutil.copy2(ROOT / "install.ps1", bundle / "install.ps1")
        shutil.copy2(ROOT / "Install-Insane-Search.cmd", bundle / "Install-Insane-Search.cmd")
    elif system == "macos":
        shutil.copy2(ROOT / "install.command", bundle / "install.command")
    readme_source = ROOT / "README-DISTRIBUTION.md"
    if not readme_source.exists():
        readme_source = ROOT / "README.md"
    shutil.copy2(readme_source, bundle / "README.md")

    skill_zip = bundle / "skill.zip"
    shutil.make_archive(str(skill_zip.with_suffix("")), "zip", root_dir=bundle / "skill", base_dir="insane-search")

    manifest = {
        "name": "insane-search",
        "version": "0.18.0-local",
        "platform": system,
        "arch": arch,
        "runtime_entry": f"runtime/{binary_name}",
        "includes": ["local stdio MCP", "Insane Search Skill", "Codex plugin metadata", "skill.zip"],
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    archive = shutil.make_archive(str(bundle), "zip", root_dir=DIST, base_dir=bundle.name)
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

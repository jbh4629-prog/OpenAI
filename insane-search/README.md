# Insane Search — Local MCP + Skill

This package runs entirely on the user's computer. It does not require the maintainer to expose an MCP server.

## macOS

1. Unzip the release.
2. Run `chmod +x install.command && ./install.command`.
3. Restart the MCP host / Codex.
4. For ChatGPT Skills, upload the bundled `skill.zip` through the Skills UI.

## Windows x64 (primary distribution target)

1. Unzip the release.
2. Double-click `Install-Insane-Search.cmd`.
3. Restart the MCP host / Codex.
4. For ChatGPT Skills, upload the bundled `skill.zip` through the Skills UI.

Advanced/manual install: `powershell -ExecutionPolicy Bypass -File .\install.ps1`.

The end user does not need Python. `insane-search-mcp.exe` and its runtime are bundled in the release.

Browser escalation is optional. HTTP, structured, extraction, reader, continuation, and X discovery routes work without it. Browser escalation becomes available when Node.js/npm and Google Chrome are installed locally; the engine installs its Node Playwright dependency into the user's home directory only if a browser fallback is actually needed.

### Build the Windows release

On a Windows x64 build machine with Python 3.11+:

`powershell -ExecutionPolicy Bypass -File .\build-windows.ps1`

This creates and smoke-tests:

- `dist\insane-search-windows-x64.zip`
- `dist\insane-search-windows-x64.sha256`

Alternatively, push this project to GitHub and run the bundled `Build Windows x64 release` workflow. It uses `windows-latest` and returns the same ZIP as a GitHub Actions artifact.

## Security model

- MCP transport is local `stdio`; there is no listening network port.
- Retrieval is read-only and targets public HTTP(S) resources.
- Returned web content is treated as untrusted data.
- CAPTCHA, authentication, and access-control bypass are not performed.
- Local continuation state is stored in the user's application-data directory.

## Build

Use Python 3.11+ with the Insane Search dependencies installed, then run:

`python scripts/build_release.py --clean`

PyInstaller produces an OS/architecture-specific `onedir` runtime, so build Windows releases on Windows and macOS releases on macOS.

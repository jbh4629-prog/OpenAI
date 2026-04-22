# Ouroboros Codex Port

A focused port of the `Q00/ouroboros` idea into a Codex-CLI-native workflow.

This implementation does **not** attempt to clone the original project 1:1. Instead, it preserves the core loop that matters for repository work:

1. **Interview** — expose ambiguity before coding
2. **Seed** — crystallize the brief into an immutable implementation spec
3. **Plan** — generate a repo-level execution plan
4. **Evaluate** — critique the plan against the seed
5. **Implement** — emit a Codex-ready prompt for direct repo execution

## Why this port exists

The upstream project is built around a Claude Code plugin, MCP integration, and a broad Python package surface. This repository already provisions **Codex CLI** in the dev container, so the most practical adaptation is a Python orchestrator that shells out to Codex instead of assuming a Claude Code runtime.

## Backend policy

This port uses **Codex CLI only**.

- no OpenAI API client integration
- no LiteLLM or provider abstraction layer
- no model SDK wiring inside the repository
- only local CLI invocation via `subprocess` to the installed `codex` binary

## What is implemented

- Typer-based CLI with `ooo` entrypoint
- Codex subprocess backend with configurable command template
- Local session artifact store under `.ouroboros/sessions/<session_id>/`
- JSON artifact generation for interview, seed, plan, and evaluation phases
- Repo-implementation prompt emission for handoff to Codex CLI

## What is intentionally out of scope

- Claude plugin packaging
- MCP server registration
- Full parity with the upstream agent graph
- TUI dashboard, event sourcing database, or multi-model consensus router
- API-based provider integrations

## Installation

```bash
uv sync
```

## Basic usage

```bash
# 1) expose ambiguity
ooo interview "Build a task management CLI" --cwd /workspaces/OpenAI

# 2) generate an immutable seed
ooo seed "Build a task management CLI" --cwd /workspaces/OpenAI

# 3) create an execution plan
ooo plan <session_id> --cwd /workspaces/OpenAI

# 4) critique the plan
ooo evaluate <session_id> --cwd /workspaces/OpenAI

# 5) emit a repo-ready implementation prompt
ooo emit-implement-prompt <session_id>
```

## One-shot flow

```bash
ooo loop "Port the Ouroboros workflow to this repo using Codex CLI" --cwd /workspaces/OpenAI
```

Artifacts land in:

```text
.ouroboros/
  sessions/
    <session_id>/
      interview.json
      seed.json
      plan.json
      evaluation.json
      implement.prompt.txt
      *.raw.txt
      *.prompt.txt
```

## Codex backend configuration

The backend defaults to:

```bash
codex exec <prompt>
```

If your Codex CLI build expects a different invocation, set a command template:

```bash
export OURO_CODEX_COMMAND_TEMPLATE='codex exec --input {prompt_file}'
```

Supported placeholders:

- `{prompt}`
- `{prompt_file}`
- `{cwd}`

You can also override the executable path:

```bash
export OURO_CODEX_EXECUTABLE=/custom/path/to/codex
```

## Notes on fidelity vs portability

The upstream README describes a specification-first loop with interview, seed, execution, and evaluation phases, plus a Typer CLI and provider abstraction. This port preserves those conceptual phases while replacing the Claude-oriented runtime with a **Codex CLI subprocess backend** and a much smaller surface area.
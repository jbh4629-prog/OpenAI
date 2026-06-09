import assert from "node:assert/strict"
import { existsSync, readFileSync } from "node:fs"
import { join } from "node:path"
import { spawnSync } from "node:child_process"
import { describe, it } from "node:test"
import { buildCommandArgs, normalizeCodexConfig } from "../bin/lazycodex-ai.js"

const root = new URL("..", import.meta.url).pathname
const packageJsonPath = join(root, "package.json")
const binPath = join(root, "bin", "lazycodex-ai.js")
const releaseVersion = "0.2.2"

describe("lazycodex-ai npm package", () => {
  it("maps the package name and bin to lazycodex-ai", () => {
    assert.equal(existsSync(packageJsonPath), true, "root package.json must exist")

    const manifest = JSON.parse(readFileSync(packageJsonPath, "utf8"))

    assert.equal(manifest.name, "lazycodex-ai")
    assert.equal(manifest.version, releaseVersion)
    assert.equal(manifest.bin?.["lazycodex-ai"], "bin/lazycodex-ai.js")
    assert.equal(manifest.private, undefined)
  })

  it("dry-runs install through oh-my-openagent with the Codex platform default", () => {
    assert.equal(existsSync(binPath), true, "lazycodex-ai bin must exist")

    const result = spawnSync(
      process.execPath,
      [binPath, "--dry-run", "install", "--no-tui", "--codex-autonomous"],
      { cwd: root, encoding: "utf8" },
    )

    assert.equal(result.status, 0, result.stderr)
    assert.equal(
      result.stdout.trim(),
      "npx --yes --package oh-my-openagent omo install --platform=codex --no-tui --codex-autonomous",
    )
  })

  it("dry-runs non-install commands through oh-my-openagent", () => {
    assert.equal(existsSync(binPath), true, "lazycodex-ai bin must exist")

    const result = spawnSync(process.execPath, [binPath, "--dry-run", "doctor"], {
      cwd: root,
      encoding: "utf8",
    })

    assert.equal(result.status, 0, result.stderr)
    assert.equal(result.stdout.trim(), "npx --yes --package oh-my-openagent omo doctor")
  })

  it("builds install commands without enabling multi_agent_v2 explicitly", () => {
    const { commandArgs } = buildCommandArgs(["install", "--no-tui", "--codex-autonomous"])

    assert.deepEqual(commandArgs, [
      "--yes",
      "--package",
      "oh-my-openagent",
      "omo",
      "install",
      "--platform=codex",
      "--no-tui",
      "--codex-autonomous",
    ])
    assert.equal(commandArgs.includes("--enable"), false)
    assert.equal(commandArgs.includes("multi_agent_v2"), false)
  })

  it("removes unsafe multi_agent_v2 force-enable settings from Codex config", () => {
    const input = `model = "gpt-5.5"

[features]
multi_agent = true
multi_agent_v2 = true
child_agents_md = true

[features.multi_agent_v2]
enabled = true
max_concurrent_threads_per_session = 7

[agents]
max_threads = 7
`

    const normalized = normalizeCodexConfig(input)

    assert.match(normalized, /\[features\]\nmulti_agent = true\nchild_agents_md = true/)
    assert.doesNotMatch(normalized, /^multi_agent_v2\s*=/m)
    assert.match(normalized, /\[features\.multi_agent_v2\]\nmax_concurrent_threads_per_session = 10000/)
    assert.doesNotMatch(normalized, /^enabled\s*=/m)
    assert.doesNotMatch(normalized, /^max_threads\s*=/m)
  })

  it("adds a safe multi_agent_v2 tuning section without turning the feature on", () => {
    const normalized = normalizeCodexConfig(`[features]\nmulti_agent = true\n`)

    assert.match(normalized, /\[features\.multi_agent_v2\]\nmax_concurrent_threads_per_session = 10000/)
    assert.doesNotMatch(normalized, /^enabled\s*=\s*true/m)
    assert.doesNotMatch(normalized, /^multi_agent_v2\s*=\s*true/m)
  })
})

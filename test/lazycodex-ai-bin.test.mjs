import assert from "node:assert/strict"
import { existsSync, readFileSync } from "node:fs"
import { join } from "node:path"
import { spawnSync } from "node:child_process"
import { describe, it } from "node:test"

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
})

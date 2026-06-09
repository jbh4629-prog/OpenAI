#!/usr/bin/env node

import { spawnSync } from "node:child_process"

const args = process.argv.slice(2)
const dryRun = args[0] === "--dry-run"
const forwardedArgs = dryRun ? args.slice(1) : args
const commandArgs =
  forwardedArgs[0] === "install"
    ? [
        "--yes",
        "--package",
        "oh-my-openagent",
        "omo",
        "install",
        "--platform=codex",
        ...forwardedArgs.slice(1),
      ]
    : ["--yes", "--package", "oh-my-openagent", "omo", ...forwardedArgs]

if (dryRun) {
  console.log(["npx", ...commandArgs].join(" "))
  process.exit(0)
}

const result = spawnSync("npx", commandArgs, {
  stdio: "inherit",
})

if (result.error) {
  console.error(result.error.message)
  process.exit(1)
}

process.exit(result.status ?? 1)

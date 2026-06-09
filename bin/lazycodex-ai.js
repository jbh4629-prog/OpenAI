#!/usr/bin/env node

import { spawnSync } from "node:child_process"
import { realpathSync } from "node:fs"
import { readFile, writeFile } from "node:fs/promises"
import { homedir } from "node:os"
import { join } from "node:path"
import { fileURLToPath } from "node:url"

const maxConcurrentThreadsPerSession = 10000

export function buildCommandArgs(args) {
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

  return { commandArgs, dryRun, forwardedArgs }
}

function isSectionHeader(line) {
  return /^\s*\[[^\]]+\]\s*(?:#.*)?$/.test(line)
}

function sectionName(line) {
  const match = line.match(/^\s*\[([^\]]+)\]\s*(?:#.*)?$/)
  return match?.[1] ?? null
}

function isSetting(line, key) {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  return new RegExp(`^\\s*${escaped}\\s*=`).test(line)
}

function replaceOrInsertSetting(lines, sectionStart, key, value) {
  let insertAt = lines.length
  for (let i = sectionStart + 1; i < lines.length; i += 1) {
    if (isSectionHeader(lines[i])) {
      insertAt = i
      break
    }
    if (isSetting(lines[i], key)) {
      lines[i] = `${key} = ${value}`
      return lines
    }
  }

  lines.splice(insertAt, 0, `${key} = ${value}`)
  return lines
}

export function normalizeCodexConfig(config) {
  const hadTrailingNewline = config.endsWith("\n")
  const lines = config.split(/\r?\n/)
  if (lines.at(-1) === "") {
    lines.pop()
  }

  let currentSection = null
  const normalized = []

  for (const line of lines) {
    const nextSection = sectionName(line)
    if (nextSection !== null) {
      currentSection = nextSection
      normalized.push(line)
      continue
    }

    if (currentSection === "features" && isSetting(line, "multi_agent_v2")) {
      continue
    }

    if (currentSection === "features.multi_agent_v2" && isSetting(line, "enabled")) {
      continue
    }

    if (currentSection === "agents" && isSetting(line, "max_threads")) {
      continue
    }

    normalized.push(line)
  }

  let multiAgentV2Section = -1
  for (let i = 0; i < normalized.length; i += 1) {
    if (sectionName(normalized[i]) === "features.multi_agent_v2") {
      multiAgentV2Section = i
      break
    }
  }

  if (multiAgentV2Section === -1) {
    if (normalized.length > 0 && normalized.at(-1) !== "") {
      normalized.push("")
    }
    normalized.push("[features.multi_agent_v2]")
    normalized.push(`max_concurrent_threads_per_session = ${maxConcurrentThreadsPerSession}`)
  } else {
    replaceOrInsertSetting(
      normalized,
      multiAgentV2Section,
      "max_concurrent_threads_per_session",
      String(maxConcurrentThreadsPerSession),
    )
  }

  return `${normalized.join("\n")}${hadTrailingNewline ? "\n" : ""}`
}

function codexConfigPath() {
  if (process.env.CODEX_CONFIG_PATH) {
    return process.env.CODEX_CONFIG_PATH
  }

  const codexHome = process.env.CODEX_HOME || join(homedir(), ".codex")
  return join(codexHome, "config.toml")
}

export async function repairCodexConfig(configPath = codexConfigPath()) {
  let config
  try {
    config = await readFile(configPath, "utf8")
  } catch (error) {
    if (error?.code === "ENOENT") {
      return false
    }
    throw error
  }

  const normalized = normalizeCodexConfig(config)
  if (normalized !== config) {
    await writeFile(configPath, normalized, "utf8")
    return true
  }

  return false
}

async function main() {
  const { commandArgs, dryRun, forwardedArgs } = buildCommandArgs(process.argv.slice(2))

  if (dryRun) {
    console.log(["npx", ...commandArgs].join(" "))
    return 0
  }

  const result = spawnSync("npx", commandArgs, {
    stdio: "inherit",
  })

  if (result.error) {
    console.error(result.error.message)
    return 1
  }

  const status = result.status ?? 1
  if (status !== 0) {
    return status
  }

  if (forwardedArgs[0] === "install") {
    await repairCodexConfig()
  }

  return 0
}

if (
  process.argv[1] &&
  realpathSync(fileURLToPath(import.meta.url)) === realpathSync(process.argv[1])
) {
  main()
    .then((status) => {
      process.exit(status)
    })
    .catch((error) => {
      console.error(error.stack || error.message || String(error))
      process.exit(1)
    })
}

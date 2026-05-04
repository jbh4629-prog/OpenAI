# Codex Skills Repo

Private source-of-truth repo for Codex skills and optional local plugins.

## Layout

- `skills/`: Codex skills to install into `$CODEX_HOME/skills`
- `plugins/`: optional local plugins to install into `~/plugins`
- `scripts/bootstrap.sh`: links or copies the repo contents into the active machine
- `install.sh`: GitHub Codespaces dotfiles entrypoint that installs these skills automatically

## Recommended workflow

1. Clone this repo on each PC.
2. Run `scripts/bootstrap.sh` once.
3. Update the repo with `git pull`.
4. Re-run `scripts/bootstrap.sh` only when new skills or plugins were added.

## Codespaces auto-install across repositories

To make these skills available in every new GitHub Codespace, configure this repository as your Codespaces dotfiles repository:

1. Open GitHub Settings.
2. Go to Codespaces.
3. Find Dotfiles.
4. Enable automatic dotfiles installation.
5. Select this repository: `jbh4629-prog/OpenAI`.

When a new Codespace starts, GitHub Codespaces runs `install.sh`. The installer then:

1. Resolves the active skills source.
2. Installs skills into `${CODEX_HOME:-$HOME/.codex}/skills`.
3. Uses copy mode by default so the working repository is not polluted and symlinks do not break when paths change.

After creating a Codespace, verify installation with:

```bash
find ~/.codex/skills -maxdepth 2 -name SKILL.md -print
```

Then run Codex:

```bash
codex
```

Invoke skills with natural language, for example:

```text
crawl-naver-blog skill을 써서 "보관이사" 네이버 블로그 공개 글 10개를 수집하고 요약해줘.
```

### Dotfiles installer environment variables

`install.sh` supports these optional environment variables:

- `CODEX_HOME`: Codex home directory. Defaults to `$HOME/.codex`.
- `CODEX_SKILLS_INSTALL_MODE`: `copy`, `link`, or `symlink`. Defaults to `copy`.
- `CODEX_SKILLS_WITH_PLUGINS`: `true` or `false`. Defaults to `false`.
- `CODEX_SKILLS_REPO_URL`: repo URL to clone when the installer is not already running from this repo.
- `CODEX_SKILLS_REPO_DIR`: local clone path. Defaults to `$HOME/codex-skills/OpenAI`.

## Default install mode

The bootstrap script uses symlinks by default.

- Pros: updates propagate after `git pull`
- Cons: the repo must stay on a path that remains valid on that machine

Use `--copy` if you want a one-time copy instead of symlinks.

## Example

```bash
bash scripts/bootstrap.sh
bash scripts/bootstrap.sh --with-plugins
bash scripts/bootstrap.sh --copy
```

## Notes

- Skills are installed into `${CODEX_HOME:-$HOME/.codex}/skills`
- Plugins are linked into `~/plugins`
- Keep the repo private if the skills include internal procedures, tokens, or company-specific logic

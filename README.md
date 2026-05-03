# Codex Skills Repo

Private source-of-truth repo for Codex skills and optional local plugins.

## Layout

- `skills/`: Codex skills to install into `$CODEX_HOME/skills`
- `plugins/`: optional local plugins to install into `~/plugins`
- `scripts/bootstrap.sh`: links or copies the repo contents into the active machine

## Recommended workflow

1. Clone this repo on each PC.
2. Run `scripts/bootstrap.sh` once.
3. Update the repo with `git pull`.
4. Re-run `scripts/bootstrap.sh` only when new skills or plugins were added.

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

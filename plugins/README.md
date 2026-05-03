# Plugins

Optional local Codex plugins live here.

## Layout

Each plugin should follow the `plugin-creator` structure:

- `<plugin-name>/.codex-plugin/plugin.json`
- optional `skills/`
- optional `scripts/`
- optional `assets/`

## Bootstrap behavior

`scripts/bootstrap.sh --with-plugins` links valid plugin folders into `~/plugins`.

Use this folder only for plugin source. Keep the repo private if the plugins contain internal logic or credentials.

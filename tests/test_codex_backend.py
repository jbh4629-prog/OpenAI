from ouroboros_codex.codex_backend import extract_json_object


def test_extract_json_object_from_fenced_block() -> None:
    raw = '```json\n{"ok": true, "value": 1}\n```'
    payload = extract_json_object(raw)
    assert payload == {"ok": True, "value": 1}

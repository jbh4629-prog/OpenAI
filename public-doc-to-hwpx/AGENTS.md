# public-doc-to-hwpx

Codex에서는 이 파일을 진입점으로 사용합니다. 상세 규격과 역사적 배경은 `SKILL.md`, 양식별 세부 규칙은 `references/`를 기준으로 따릅니다.

## 목적

- AI가 만든 초안을 공공기관 표준 문체로 다듬는다.
- 결과물은 `format_1p`, `format_full`, `format_gongmun` HWPX 또는 이메일 본문 텍스트다.
- HWPX는 내장 `skeleton.hwpx`에 값만 채우는 방식으로 빌드한다. 양식의 표·테두리·음영·헤더를 다시 만들지 않는다.

## 기본 워크플로우

1. 사용자에게 참조 `.hwpx`가 있는지 먼저 확인한다.
2. 있으면 "서식만 반영 / 서식+내용 반영" 중 무엇인지 한 번 더 묻는다.
3. 없으면 `references/format-selection.md`와 입력 분량을 보고 양식을 추천한다.
4. 선택된 양식의 `templates/<format>/skeleton_mapping.json`을 읽고 `values.json` 형태로 내용을 정리한다.
5. 빌드는 아래 표준 명령을 사용한다.
6. 1p가 1쪽을 넘길 정도로 길면 자동으로 풀버전으로 바꾸지 말고 사용자에게 먼저 권고한다.

## 표준 빌드 명령

```bash
# 1페이지 보고서
python3 scripts/build_document.py \
  --format format_1p \
  --values my_values.json \
  --output out.hwpx

# 시행문
python3 scripts/build_document.py \
  --format format_gongmun \
  --values my_values.json \
  --output out.hwpx

# 풀버전 보고서
python3 scripts/build_document.py \
  --format format_full \
  --values my_values.json \
  --output out.hwpx
```

`build_document.py`가 양식별 표준 후처리와 `validate.py`까지 수행합니다. `format_full`은 내부적으로 `build_full.py`를 호출합니다.

## 꼭 지킬 규칙

- 삭제된 `compose_doc.py`, `layout_optimizer.py`를 다시 전제로 두지 않는다.
- HWPX 출력은 항상 표준 스크립트 경로로 만든다. 수동 XML 조립은 금지한다.
- `format_full`은 `build_full.py` 계열 파이프라인을 사용한다. 목차 페이지번호는 2-pass 빌드가 필요하다.
- `format_gongmun` 메타 항목(시행번호, 날짜, 전화 등)은 사용자가 주지 않으면 빈 값으로 둔다.
- `format_1p`는 `templates/format_1p/outline_guide.md`의 11개 표준 목차를 우선 적용한다.

## 빠른 점검 명령

```bash
python3 scripts/build_document.py --format format_1p --values examples/example_values_1p.json --output /tmp/example_1p.hwpx
python3 scripts/build_document.py --format format_gongmun --values examples/example_values_gongmun.json --output /tmp/example_gongmun.hwpx
python3 scripts/build_document.py --format format_full --values examples/example_values_full.json --output /tmp/example_full.hwpx
```

## 참고 문서

- 전체 워크플로우: `SKILL.md`
- 글쓰기 기준: `references/writing-principles.md`
- 레이아웃 기준: `references/layout-rules.md`
- 양식 선택: `references/format-selection.md`

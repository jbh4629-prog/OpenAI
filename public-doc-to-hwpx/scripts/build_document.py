"""
build_document.py — Codex/CLI용 통합 빌드 진입점 (v3.7.0 신규)
────────────────────────────────────────────────────────────────
현재 리포지토리의 표준 빌드 스크립트를 한 명령으로 묶는다.

지원 양식:
  - format_1p
  - format_gongmun
  - format_full

사용법:
    python build_document.py \
        --format format_1p \
        --values examples/example_values_1p.json \
        --output out.hwpx

    python build_document.py \
        --format format_gongmun \
        --values examples/example_values_gongmun.json \
        --output out.hwpx

    python build_document.py \
        --format format_full \
        --values examples/example_values_full.json \
        --output out.hwpx

특징:
  - format_1p: fill_skeleton → fix_namespaces → validate
  - format_gongmun: fill_skeleton → fix_namespaces → fix_gongmun_body → validate
  - format_full: build_full.py 위임 (2-pass + 후처리 전체)
────────────────────────────────────────────────────────────────
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent

DEFAULT_SKELETONS = {
    "format_1p": ROOT_DIR / "templates" / "format_1p" / "skeleton.hwpx",
    "format_gongmun": ROOT_DIR / "templates" / "format_gongmun" / "skeleton.hwpx",
    "format_full": ROOT_DIR / "templates" / "format_full" / "skeleton.hwpx",
}

DEFAULT_MAPPINGS = {
    "format_full": ROOT_DIR / "templates" / "format_full" / "skeleton_mapping.json",
}


def run_script(script_name: str, *args: str) -> None:
    cmd = [sys.executable, str(SCRIPT_DIR / script_name), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        raise SystemExit(result.returncode)


def build_simple(format_name: str, skeleton: Path, values: Path, output: Path) -> None:
    print(f"===== {format_name} 빌드 시작 =====")
    run_script("fill_skeleton.py",
               "--skeleton", str(skeleton),
               "--values", str(values),
               "--output", str(output))
    run_script("fix_namespaces.py", str(output))
    if format_name == "format_gongmun":
        run_script("fix_gongmun_body.py", str(output))
    run_script("validate.py", str(output))
    print(f"✅ 완료: {output}")


def build_full(values: Path, output: Path, skeleton: Path,
               mapping: Path, strict: bool) -> None:
    print("===== format_full 빌드 시작 =====")
    args = [
        "--values", str(values),
        "--output", str(output),
        "--skeleton", str(skeleton),
        "--mapping", str(mapping),
    ]
    if strict:
        args.append("--strict")
    run_script("build_full.py", *args)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="public-doc-to-hwpx 통합 빌드 진입점")
    parser.add_argument("--format", required=True,
                        choices=["format_1p", "format_gongmun", "format_full"],
                        help="빌드할 양식")
    parser.add_argument("--values", required=True,
                        help="values.json 경로")
    parser.add_argument("--output", required=True,
                        help="출력 hwpx 경로")
    parser.add_argument("--skeleton",
                        help="사용할 skeleton.hwpx 경로 (기본: 양식별 내장)")
    parser.add_argument("--mapping",
                        help="format_full용 skeleton_mapping.json 경로")
    parser.add_argument("--strict", action="store_true",
                        help="format_full 입력 위반 발견 시 빌드 중단")
    args = parser.parse_args()

    format_name = args.format
    values = Path(args.values).resolve()
    output = Path(args.output).resolve()
    skeleton = Path(args.skeleton).resolve() if args.skeleton else DEFAULT_SKELETONS[format_name]

    if format_name == "format_full":
        mapping = Path(args.mapping).resolve() if args.mapping else DEFAULT_MAPPINGS["format_full"]
        build_full(values, output, skeleton, mapping, args.strict)
        return

    build_simple(format_name, skeleton, values, output)


if __name__ == "__main__":
    main()

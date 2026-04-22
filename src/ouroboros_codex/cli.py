from __future__ import annotations

from pathlib import Path
from typing import Annotated
import json
import uuid

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .codex_backend import CodexBackend, CodexBackendError
from .models import EvaluationReport, ExecutionPlan, InterviewReport, SeedSpec
from .store import SessionStore
from .workflow import WorkflowEngine

app = typer.Typer(help="Ouroboros-style specification workflow powered by Codex CLI")
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"ouroboros-codex {__version__}")
        raise typer.Exit()


def make_engine(cwd: str | None = None) -> WorkflowEngine:
    return WorkflowEngine(backend=CodexBackend(cwd=cwd), store=SessionStore())


def read_text_file(path: Path | None) -> str | None:
    return None if path is None else path.read_text(encoding="utf-8")


def print_interview(report: InterviewReport) -> None:
    console.print(f"[bold]Ambiguity[/]: {report.ambiguity:.2f} | [bold]Readiness[/]: {report.readiness}")
    if report.hidden_assumptions:
        console.print("\n[bold]Hidden assumptions[/]")
        for item in report.hidden_assumptions:
            console.print(f"- {item}")
    table = Table(title="Interview questions")
    table.add_column("Dimension")
    table.add_column("Weight")
    table.add_column("Question")
    table.add_column("Rationale")
    for q in report.questions:
        table.add_row(q.dimension, f"{q.weight:.2f}", q.question, q.rationale)
    console.print(table)


def print_seed(spec: SeedSpec) -> None:
    console.print(f"[bold]{spec.title}[/]")
    console.print(spec.problem)
    sections = {
        "Goals": spec.goals,
        "Non-goals": spec.non_goals,
        "Constraints": spec.constraints,
        "Acceptance criteria": spec.acceptance_criteria,
        "Risks": spec.risks,
        "Artifacts": spec.artifacts,
        "Implementation notes": spec.implementation_notes,
    }
    for title, items in sections.items():
        if items:
            console.print(f"\n[bold]{title}[/]")
            for item in items:
                console.print(f"- {item}")


def print_plan(plan: ExecutionPlan) -> None:
    console.print(f"[bold]Plan summary[/]\n{plan.summary}")
    sections = {
        "Workstreams": plan.workstreams,
        "File plan": plan.file_plan,
        "Milestones": plan.milestones,
        "Codex prompts": plan.prompts_for_codex,
        "Verification": plan.verification_steps,
    }
    for title, items in sections.items():
        if items:
            console.print(f"\n[bold]{title}[/]")
            for item in items:
                console.print(f"- {item}")


def print_evaluation(report: EvaluationReport) -> None:
    console.print(f"[bold]Verdict[/]: {report.verdict} | [bold]Confidence[/]: {report.confidence:.2f}")
    sections = {
        "Strengths": report.strengths,
        "Gaps": report.gaps,
        "Follow-ups": report.follow_ups,
    }
    for title, items in sections.items():
        if items:
            console.print(f"\n[bold]{title}[/]")
            for item in items:
                console.print(f"- {item}")


def resolve_session_id(explicit: str | None) -> str:
    return explicit or uuid.uuid4().hex[:8]


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    _ = version


@app.command()
def interview(
    brief: Annotated[str, typer.Argument(help="Project brief to interrogate")],
    session: Annotated[str | None, typer.Option("--session", help="Existing or new session id")] = None,
    context_file: Annotated[Path | None, typer.Option("--context-file", help="Optional context markdown/txt file")] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory passed to Codex CLI")] = None,
) -> None:
    engine = make_engine(cwd=cwd)
    session_id = resolve_session_id(session)
    try:
        report = engine.interview(session_id=session_id, brief=brief, context=read_text_file(context_file))
    except CodexBackendError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=1)
    console.print(f"[green]Session[/]: {session_id}")
    print_interview(report)


@app.command()
def seed(
    brief: Annotated[str, typer.Argument(help="Project brief to crystallize")],
    session: Annotated[str | None, typer.Option("--session", help="Existing or new session id")] = None,
    context_file: Annotated[Path | None, typer.Option("--context-file", help="Optional context markdown/txt file")] = None,
    answers_file: Annotated[Path | None, typer.Option("--answers-file", help="Optional interview answers file")] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory passed to Codex CLI")] = None,
) -> None:
    engine = make_engine(cwd=cwd)
    session_id = resolve_session_id(session)
    try:
        spec = engine.seed(session_id=session_id, brief=brief, context=read_text_file(context_file), answers=read_text_file(answers_file))
    except CodexBackendError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=1)
    console.print(f"[green]Session[/]: {session_id}")
    print_seed(spec)


@app.command("plan")
def plan_command(
    session: Annotated[str, typer.Argument(help="Session id containing seed.json")],
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory passed to Codex CLI")] = None,
) -> None:
    engine = make_engine(cwd=cwd)
    try:
        spec = SeedSpec.from_dict(engine.store.read_json(session, "seed.json"))
        plan = engine.plan(session_id=session, seed=spec)
    except FileNotFoundError:
        console.print("[red]seed.json not found for that session.[/]")
        raise typer.Exit(code=1)
    except CodexBackendError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=1)
    print_plan(plan)


@app.command()
def evaluate(
    session: Annotated[str, typer.Argument(help="Session id containing seed.json and plan.json")],
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory passed to Codex CLI")] = None,
) -> None:
    engine = make_engine(cwd=cwd)
    try:
        spec = SeedSpec.from_dict(engine.store.read_json(session, "seed.json"))
        plan = ExecutionPlan.from_dict(engine.store.read_json(session, "plan.json"))
        report = engine.evaluate(session_id=session, seed=spec, plan=plan)
    except FileNotFoundError as exc:
        console.print(f"[red]Missing prerequisite file: {exc.filename}[/]")
        raise typer.Exit(code=1)
    except CodexBackendError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=1)
    print_evaluation(report)


@app.command()
def loop(
    brief: Annotated[str, typer.Argument(help="Project brief")],
    session: Annotated[str | None, typer.Option("--session", help="Existing or new session id")] = None,
    context_file: Annotated[Path | None, typer.Option("--context-file", help="Optional context markdown/txt file")] = None,
    answers_file: Annotated[Path | None, typer.Option("--answers-file", help="Optional interview answers file")] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory passed to Codex CLI")] = None,
) -> None:
    engine = make_engine(cwd=cwd)
    session_id = resolve_session_id(session)
    try:
        interview_report = engine.interview(session_id=session_id, brief=brief, context=read_text_file(context_file))
        spec = engine.seed(session_id=session_id, brief=brief, context=read_text_file(context_file), answers=read_text_file(answers_file))
        plan = engine.plan(session_id=session_id, seed=spec)
        evaluation = engine.evaluate(session_id=session_id, seed=spec, plan=plan)
        impl_path = engine.implementation_prompt(session_id=session_id, seed=spec, plan=plan)
    except CodexBackendError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=1)
    console.print(f"[green]Session[/]: {session_id}")
    print_interview(interview_report)
    console.print()
    print_seed(spec)
    console.print()
    print_plan(plan)
    console.print()
    print_evaluation(evaluation)
    console.print(f"\n[bold]Repo implementation prompt[/]: {impl_path}")


@app.command()
def status(session: Annotated[str, typer.Argument(help="Session id")]) -> None:
    store = SessionStore()
    files = store.list_session_files(session)
    if not files:
        console.print("[red]No files found for that session.[/]")
        raise typer.Exit(code=1)
    table = Table(title=f"Session {session}")
    table.add_column("File")
    table.add_column("Type")
    table.add_column("Preview")
    for path in files:
        preview = path.read_text(encoding="utf-8")[:120].replace("\n", " ")
        table.add_row(path.name, path.suffix or "(none)", preview)
    console.print(table)


@app.command("emit-implement-prompt")
def emit_implement_prompt(session: Annotated[str, typer.Argument(help="Session id containing seed.json and plan.json")]) -> None:
    store = SessionStore()
    try:
        seed = SeedSpec.from_dict(store.read_json(session, "seed.json"))
        plan = ExecutionPlan.from_dict(store.read_json(session, "plan.json"))
    except FileNotFoundError as exc:
        console.print(f"[red]Missing prerequisite file: {exc.filename}[/]")
        raise typer.Exit(code=1)
    path = WorkflowEngine(backend=CodexBackend(), store=store).implementation_prompt(session, seed, plan)
    console.print(path)


@app.command()
def cat(
    session: Annotated[str, typer.Argument(help="Session id")],
    name: Annotated[str, typer.Argument(help="Artifact file name, e.g. seed.json")],
) -> None:
    path = SessionStore().session_dir(session) / name
    if not path.exists():
        console.print("[red]Artifact not found.[/]")
        raise typer.Exit(code=1)
    if path.suffix == ".json":
        console.print_json(data=json.loads(path.read_text(encoding="utf-8")))
    else:
        console.print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    app()

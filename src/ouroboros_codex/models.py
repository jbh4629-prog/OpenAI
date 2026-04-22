from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class InterviewQuestion:
    question: str
    rationale: str
    dimension: str
    weight: float


@dataclass(slots=True)
class InterviewReport:
    brief: str
    context: str | None
    ambiguity: float
    readiness: str
    hidden_assumptions: list[str]
    questions: list[InterviewQuestion]
    created_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InterviewReport":
        return cls(
            brief=data["brief"],
            context=data.get("context"),
            ambiguity=float(data["ambiguity"]),
            readiness=str(data["readiness"]),
            hidden_assumptions=[str(x) for x in data.get("hidden_assumptions", [])],
            questions=[InterviewQuestion(**q) for q in data.get("questions", [])],
            created_at=str(data.get("created_at") or utc_now_iso()),
        )


@dataclass(slots=True)
class SeedSpec:
    title: str
    problem: str
    users: list[str]
    goals: list[str]
    non_goals: list[str]
    constraints: list[str]
    acceptance_criteria: list[str]
    risks: list[str]
    artifacts: list[str]
    implementation_notes: list[str]
    source_brief: str
    created_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SeedSpec":
        return cls(
            title=str(data["title"]),
            problem=str(data["problem"]),
            users=[str(x) for x in data.get("users", [])],
            goals=[str(x) for x in data.get("goals", [])],
            non_goals=[str(x) for x in data.get("non_goals", [])],
            constraints=[str(x) for x in data.get("constraints", [])],
            acceptance_criteria=[str(x) for x in data.get("acceptance_criteria", [])],
            risks=[str(x) for x in data.get("risks", [])],
            artifacts=[str(x) for x in data.get("artifacts", [])],
            implementation_notes=[str(x) for x in data.get("implementation_notes", [])],
            source_brief=str(data.get("source_brief", "")),
            created_at=str(data.get("created_at") or utc_now_iso()),
        )


@dataclass(slots=True)
class ExecutionPlan:
    summary: str
    workstreams: list[str]
    file_plan: list[str]
    milestones: list[str]
    prompts_for_codex: list[str]
    verification_steps: list[str]
    created_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionPlan":
        return cls(
            summary=str(data["summary"]),
            workstreams=[str(x) for x in data.get("workstreams", [])],
            file_plan=[str(x) for x in data.get("file_plan", [])],
            milestones=[str(x) for x in data.get("milestones", [])],
            prompts_for_codex=[str(x) for x in data.get("prompts_for_codex", [])],
            verification_steps=[str(x) for x in data.get("verification_steps", [])],
            created_at=str(data.get("created_at") or utc_now_iso()),
        )


@dataclass(slots=True)
class EvaluationReport:
    verdict: str
    strengths: list[str]
    gaps: list[str]
    follow_ups: list[str]
    confidence: float
    created_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationReport":
        return cls(
            verdict=str(data["verdict"]),
            strengths=[str(x) for x in data.get("strengths", [])],
            gaps=[str(x) for x in data.get("gaps", [])],
            follow_ups=[str(x) for x in data.get("follow_ups", [])],
            confidence=float(data.get("confidence", 0.0)),
            created_at=str(data.get("created_at") or utc_now_iso()),
        )

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

from .codex_backend import CodexBackend, extract_json_object
from .models import EvaluationReport, ExecutionPlan, InterviewReport, SeedSpec
from .prompts import direct_repo_implementation_prompt, evaluation_prompt, execution_prompt, interview_prompt, seed_prompt
from .store import SessionStore


class WorkflowEngine:
    def __init__(self, backend: CodexBackend, store: SessionStore) -> None:
        self.backend = backend
        self.store = store

    def interview(self, session_id: str, brief: str, context: str | None = None) -> InterviewReport:
        prompt = interview_prompt(brief=brief, context=context)
        raw = self.backend.run(prompt).stdout
        report = InterviewReport.from_dict(extract_json_object(raw))
        self.store.write_json(session_id, "interview.json", report)
        self.store.write_text(session_id, "interview.prompt.txt", prompt)
        self.store.write_text(session_id, "interview.raw.txt", raw)
        return report

    def seed(self, session_id: str, brief: str, context: str | None = None, answers: str | None = None) -> SeedSpec:
        prompt = seed_prompt(brief=brief, context=context, answers=answers)
        raw = self.backend.run(prompt).stdout
        spec = SeedSpec.from_dict(extract_json_object(raw))
        self.store.write_json(session_id, "seed.json", spec)
        self.store.write_text(session_id, "seed.prompt.txt", prompt)
        self.store.write_text(session_id, "seed.raw.txt", raw)
        return spec

    def plan(self, session_id: str, seed: SeedSpec) -> ExecutionPlan:
        seed_json = json.dumps(asdict(seed), ensure_ascii=False, indent=2)
        prompt = execution_prompt(seed_json)
        raw = self.backend.run(prompt).stdout
        plan = ExecutionPlan.from_dict(extract_json_object(raw))
        self.store.write_json(session_id, "plan.json", plan)
        self.store.write_text(session_id, "plan.prompt.txt", prompt)
        self.store.write_text(session_id, "plan.raw.txt", raw)
        return plan

    def evaluate(self, session_id: str, seed: SeedSpec, plan: ExecutionPlan) -> EvaluationReport:
        seed_json = json.dumps(asdict(seed), ensure_ascii=False, indent=2)
        plan_json = json.dumps(asdict(plan), ensure_ascii=False, indent=2)
        prompt = evaluation_prompt(seed_json=seed_json, plan_json=plan_json)
        raw = self.backend.run(prompt).stdout
        report = EvaluationReport.from_dict(extract_json_object(raw))
        self.store.write_json(session_id, "evaluation.json", report)
        self.store.write_text(session_id, "evaluation.prompt.txt", prompt)
        self.store.write_text(session_id, "evaluation.raw.txt", raw)
        return report

    def implementation_prompt(self, session_id: str, seed: SeedSpec, plan: ExecutionPlan) -> Path:
        seed_json = json.dumps(asdict(seed), ensure_ascii=False, indent=2)
        plan_json = json.dumps(asdict(plan), ensure_ascii=False, indent=2)
        prompt = direct_repo_implementation_prompt(seed_json=seed_json, plan_json=plan_json)
        return self.store.write_text(session_id, "implement.prompt.txt", prompt)

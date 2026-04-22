from __future__ import annotations

from textwrap import dedent


def interview_prompt(brief: str, context: str | None) -> str:
    context_block = context.strip() if context else "(none)"
    return dedent(
        f"""
        You are the interview phase of a specification-first software workflow.
        Your job is to expose ambiguity before implementation begins.

        Return STRICT JSON only with this schema:
        {{
          "brief": string,
          "context": string | null,
          "ambiguity": number,
          "readiness": "blocked" | "needs-clarification" | "ready",
          "hidden_assumptions": string[],
          "questions": [
            {{
              "question": string,
              "rationale": string,
              "dimension": "goal" | "constraint" | "success" | "context",
              "weight": number
            }}
          ]
        }}

        Rules:
        - ambiguity must be between 0.0 and 1.0
        - ask 5 to 8 questions
        - weights must sum to approximately 1.0
        - focus on product essence, constraints, scope boundaries, and measurable success
        - no markdown fences

        BRIEF:
        {brief}

        CONTEXT:
        {context_block}
        """
    ).strip()


def seed_prompt(brief: str, context: str | None, answers: str | None) -> str:
    context_block = context.strip() if context else "(none)"
    answers_block = answers.strip() if answers else "(none)"
    return dedent(
        f"""
        You are the seed architect phase of a specification-first workflow.
        Convert the brief and answers into an implementation-grade immutable seed.

        Return STRICT JSON only with this schema:
        {{
          "title": string,
          "problem": string,
          "users": string[],
          "goals": string[],
          "non_goals": string[],
          "constraints": string[],
          "acceptance_criteria": string[],
          "risks": string[],
          "artifacts": string[],
          "implementation_notes": string[],
          "source_brief": string
        }}

        Rules:
        - 3 to 7 goals
        - 3 to 7 acceptance criteria
        - artifacts should be concrete deliverables or files
        - implementation_notes should tell an engineer how to start
        - no markdown fences

        BRIEF:
        {brief}

        CONTEXT:
        {context_block}

        ANSWERS:
        {answers_block}
        """
    ).strip()


def execution_prompt(seed_json: str) -> str:
    return dedent(
        f"""
        You are the execution planner phase of a specification-first workflow.
        Use the seed below to create a repo-level implementation plan that can be executed with Codex CLI.

        Return STRICT JSON only with this schema:
        {{
          "summary": string,
          "workstreams": string[],
          "file_plan": string[],
          "milestones": string[],
          "prompts_for_codex": string[],
          "verification_steps": string[]
        }}

        Rules:
        - file_plan entries should look like paths or path groups
        - prompts_for_codex should be directly reusable as Codex tasks
        - verification_steps should be specific and testable
        - no markdown fences

        SEED:
        {seed_json}
        """
    ).strip()


def evaluation_prompt(seed_json: str, plan_json: str) -> str:
    return dedent(
        f"""
        You are the evaluation phase of a specification-first workflow.
        Assess whether the plan satisfies the seed.

        Return STRICT JSON only with this schema:
        {{
          "verdict": "accept" | "revise" | "reject",
          "strengths": string[],
          "gaps": string[],
          "follow_ups": string[],
          "confidence": number
        }}

        Rules:
        - confidence must be between 0.0 and 1.0
        - gaps should be concrete defects or ambiguities
        - follow_ups should be actionable next steps
        - no markdown fences

        SEED:
        {seed_json}

        PLAN:
        {plan_json}
        """
    ).strip()


def direct_repo_implementation_prompt(seed_json: str, plan_json: str) -> str:
    return dedent(
        f"""
        Implement the following specification in the current repository.
        Honor existing project conventions, keep changes minimal but complete,
        and create or update documentation where necessary.

        SPEC:
        {seed_json}

        EXECUTION PLAN:
        {plan_json}
        """
    ).strip()

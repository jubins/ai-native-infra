"""
Autonomous healing: diagnose, then act inside a strict scope.
Introduced in section 2.2.3 (Table 2.4) as the Autonomous Healing pattern.
Run: python autonomous_healing.py
"""
from pydantic import Field
from ch02_setup import call_with_envelope, Confidence

ALLOWED_ACTIONS = {"restart_pod", "drain_node", "rotate_secret"}

class RemediationPlan(Confidence):
    action: str = Field(description="ONE action from the allowlist, or 'page_human'")
    target: str = Field(default="")
    reason: str = ""

def page_human(assessment: str, plan: RemediationPlan | None = None) -> RemediationPlan:
    return RemediationPlan(action="page_human",
                           reason=f"escalated: {assessment}",
                           confidence=1.0)

def execute(plan: RemediationPlan) -> str:
    """In production this calls kubectl/cloud APIs. Here we just log."""
    return f"executed {plan.action} on {plan.target}"

def remediate(assessment: str) -> str:
    plan = call_with_envelope(
        prompt=(f"Given this incident assessment, propose ONE action.\n"
                f"Allowed actions: {sorted(ALLOWED_ACTIONS)} or 'page_human'.\n"
                f"Assessment: {assessment}"),
        schema=RemediationPlan,
        fallback=lambda: page_human(assessment),
    )
    if plan.action not in ALLOWED_ACTIONS:                            #A
        return execute(page_human(assessment, plan))
    if plan.confidence < 0.8:                                         #B
        return execute(page_human(assessment, plan))
    return execute(plan)

if __name__ == "__main__":
    cases = [
        "checkout-7f8c9 OOMKilled three times in 10 minutes, no recent deploy",
        "payments service returning 500s; suspected stale credential",
        "global checkout latency p95 spiked 5x; cause unknown",
    ]
    for a in cases:
        print(f"- {a[:60]:60} -> {remediate(a)}")

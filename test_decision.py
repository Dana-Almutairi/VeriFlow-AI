
import json

from backend.planning_agent import plan_research
from backend.research_agent import research_claim
from backend.verification_agent import verify_evidence
from backend.decision_agent import make_decision


claim = (
    "Artificial intelligence systems "
    "can generate false information."
)

try:
    print("STEP 1: Planning Agent...")
    plan = plan_research(claim)

    print("STEP 2: Research Agent...")
    research = research_claim(plan["queries"])

    if not research["sources"]:
        raise RuntimeError("No sources found")

    print("STEP 3: Verification Agent...")
    verification = verify_evidence(
        claim,
        research["sources"],
    )

    print("STEP 4: Decision Agent...")
    report = make_decision(
        claim,
        research["sources"],
        verification,
    )

    print()
    print("SUCCESS: All four agents completed!")
    print()

    print(json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    ))

except Exception as error:
    print("FAILED")
    print(type(error).__name__)
    print(str(error))


from backend.planning_agent import plan_research
from backend.research_agent import research_claim
from backend.verification_agent import verify_evidence

claim = "Artificial intelligence systems can generate false information."

try:
    print("STEP 1: Planning...")
    plan = plan_research(claim)

    print("STEP 2: Researching...")
    research = research_claim(plan["queries"])

    if not research["sources"]:
        raise RuntimeError("No sources found")

    print("STEP 3: Verifying evidence...")
    verification = verify_evidence(
        claim,
        research["sources"],
    )

    print()
    print("SUCCESS: Verification Agent completed!")
    print()

    for item in verification["assessments"]:
        print("SOURCE:", item["source_id"])
        print("STANCE:", item["stance"])
        print("REASON:", item["reason"])
        print()

    print("SUMMARY:", verification["summary"])

except Exception as error:
    print("FAILED")
    print(type(error).__name__)
    print(str(error))

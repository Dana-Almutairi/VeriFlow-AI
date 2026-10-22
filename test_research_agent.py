
from backend.planning_agent import plan_research
from backend.research_agent import research_claim

claim = "Artificial intelligence systems can generate false information."

try:
    print("STEP 1: Planning research...")
    plan = plan_research(claim)

    print("SUCCESS: Research plan created!")
    print()

    print("STEP 2: Searching for evidence...")
    result = research_claim(plan["queries"])

    print("TOTAL UNIQUE SOURCES:", result["total_sources"])
    print("SEARCHES COMPLETED:", len(result["search_log"]))
    print("SEARCH ERRORS:", len(result["errors"]))
    print()

    for source in result["sources"]:
        print(f"SOURCE {source['id']}: {source['title']}")
        print("URL:", source["url"])
        print()

    if result["total_sources"] > 0:
        print("SUCCESS: Research Agent is working!")
    else:
        print("WARNING: No evidence sources found.")

except Exception as error:
    print("FAILED")
    print(type(error).__name__)
    print(str(error))


from backend.planning_agent import plan_research

claim = "Artificial intelligence systems can generate false information."

try:
    plan = plan_research(claim)

    print("SUCCESS: Planning Agent is working!")
    print()
    print("CLAIM:", claim)

    for index, query in enumerate(plan["queries"], 1):
        print(f"SEARCH QUERY {index}: {query}")

except Exception as error:
    print("FAILED")
    print(type(error).__name__)
    print(str(error))

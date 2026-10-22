
from backend.verification_agent import verify_evidence

claim = "The Sun revolves around the Earth once every 24 hours."

sources = [
    {
        "id": 1,
        "title": "Apparent Solar Motion",
        "content": (
            "The sun takes a full 24 hours to make "
            "a complete circle around the celestial sphere."
        ),
    },
    {
        "id": 2,
        "title": "Earth Rotation Explanation",
        "content": (
            "The Sun appears to move across Earth's sky "
            "because Earth rotates on its axis. "
            "This apparent daily motion does not mean "
            "the Sun physically orbits Earth."
        ),
    },
    {
        "id": 3,
        "title": "Explicit Physical Claim",
        "content": (
            "The author asserts that the Sun physically "
            "revolves around Earth every 24 hours."
        ),
    },
]

expected = {
    1: "INSUFFICIENT",
    2: "CONTRADICTS",
    3: "SUPPORTS",
}

result = verify_evidence(claim, sources)

correct = 0

print("\nSOLAR MOTION VERIFICATION TEST\n")

for item in result["assessments"]:
    source_id = item["source_id"]
    actual = item["stance"]
    target = expected[source_id]

    passed = actual == target
    correct += passed

    print(f"Source {source_id}")
    print(f"Expected: {target}")
    print(f"Actual:   {actual}")
    print(f"Result:   {'PASS' if passed else 'FAIL'}")
    print(f"Reason:   {item['reason']}")
    print("-" * 45)

print(f"\nFINAL SCORE: {correct}/{len(expected)}")

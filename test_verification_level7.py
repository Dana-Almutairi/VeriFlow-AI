
from backend.verification_agent import verify_evidence

claim = "The Earth revolves around the Sun."

sources = [
    {
        "id": 1,
        "title": "Direct Supporting Evidence",
        "content": (
            "The Earth travels around the Sun "
            "in an elliptical orbit."
        ),
    },
    {
        "id": 2,
        "title": "Direct Contradicting Statement",
        "content": (
            "The Earth does not revolve around the Sun. "
            "Instead, the Sun revolves around the Earth."
        ),
    },
    {
        "id": 3,
        "title": "Apparent Motion",
        "content": (
            "From the perspective of an observer on Earth, "
            "the Sun appears to move across the sky "
            "from east to west."
        ),
    },
]

expected = {
    1: "SUPPORTS",
    2: "CONTRADICTS",
    3: "INSUFFICIENT",
}

print("\nRunning VeriFlow AI Verification Test...\n")

result = verify_evidence(claim, sources)

correct = 0

for item in result["assessments"]:
    source_id = item["source_id"]
    actual = item["stance"]
    expected_stance = expected[source_id]

    passed = actual == expected_stance

    if passed:
        correct += 1

    print(f"Source {source_id}")
    print(f"Expected: {expected_stance}")
    print(f"Actual:   {actual}")
    print(f"Result:   {'PASS' if passed else 'FAIL'}")
    print(f"Reason:   {item['reason']}")
    print("-" * 45)

print(f"\nFinal Score: {correct}/3")

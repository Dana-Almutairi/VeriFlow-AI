
from backend.verification_agent import verify_evidence

claim = "The Earth revolves around the Sun."

sources = [
    {
        "id": 1,
        "title": "Historical Belief",
        "content": (
            "Some historical societies believed that "
            "the Sun revolved around the Earth. "
            "This was a historical belief, not "
            "a statement of scientific fact."
        ),
    },
    {
        "id": 2,
        "title": "Misleading Quotation",
        "content": (
            "The sentence 'The Earth revolves around "
            "the Sun' appeared in a fictional story. "
            "The passage was discussing the wording "
            "of the sentence, not presenting evidence "
            "about astronomy."
        ),
    },
    {
        "id": 3,
        "title": "Explicit Scientific Evidence",
        "content": (
            "Astronomical measurements establish that "
            "Earth orbits the Sun approximately once "
            "every year."
        ),
    },
    {
        "id": 4,
        "title": "Explicit Denial",
        "content": (
            "The author explicitly asserts that "
            "Earth does not orbit the Sun and "
            "that the Sun instead orbits Earth."
        ),
    },
]

expected = {
    1: "INSUFFICIENT",
    2: "INSUFFICIENT",
    3: "SUPPORTS",
    4: "CONTRADICTS",
}

result = verify_evidence(claim, sources)

correct = 0

print("\nADVANCED VERIFICATION TEST\n")

for item in result["assessments"]:
    source_id = item["source_id"]
    actual = item["stance"]
    target = expected[source_id]

    passed = actual == target

    if passed:
        correct += 1

    print(f"Source {source_id}")
    print(f"Expected: {target}")
    print(f"Actual:   {actual}")
    print(f"Result:   {'PASS' if passed else 'FAIL'}")
    print(f"Reason:   {item['reason']}")
    print("-" * 45)

print(f"\nFINAL SCORE: {correct}/{len(expected)}")

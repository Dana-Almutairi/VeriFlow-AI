
from backend.decision_agent import make_decision

claim = "The Earth revolves around the Sun."

sources = [
    {
        "id": 1,
        "title": "Weak Supporting Source A",
        "url": "https://example.com/a",
        "quality_score": 0.1,
    },
    {
        "id": 2,
        "title": "Weak Supporting Source B",
        "url": "https://example.com/b",
        "quality_score": 0.1,
    },
    {
        "id": 3,
        "title": "Weak Supporting Source C",
        "url": "https://example.com/c",
        "quality_score": 0.1,
    },
    {
        "id": 4,
        "title": "Strong Contradicting Source",
        "url": "https://example.org/d",
        "quality_score": 0.95,
    },
]

verification = {
    "assessments": [
        {
            "source_id": source["id"],
            "stance": (
                "SUPPORTS"
                if source["id"] < 4
                else "CONTRADICTS"
            ),
            "reason": "Synthetic test assessment.",
            "quote": "Synthetic test quotation.",
            "quote_verified": True,
        }
        for source in sources
    ],
    "summary": "Synthetic conflicting evidence test.",
}

result = make_decision(
    claim,
    sources,
    verification,
)

print("\nDECISION AGENT TEST\n")
print("Verdict:", result["verdict"])
print("Counts:", result["evidence_counts"])
print("Metrics:", result["decision_metrics"])

expected_verdict = "CONFLICTING_EVIDENCE"

assert result["verdict"] == expected_verdict, (
    f"Expected {expected_verdict}, "
    f"but received {result['verdict']}"
)

print("\nExpected verdict:", expected_verdict)
print("Result: PASS")
print(
    "Conflicting evidence is reported without "
    "using source counts alone to select a side."
)

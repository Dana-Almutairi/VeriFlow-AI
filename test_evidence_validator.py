
from backend.evidence_validator import validate_evidence

sources = [
    {
        "id": 1,
        "title": "AI Research",
        "url": "https://example.com/research",
        "content": (
            "AI systems can generate incorrect "
            "or misleading information."
        ),
    },
    {
        "id": 2,
        "title": "Another Source",
        "url": "https://example.com/other",
        "content": "This article discusses computer hardware.",
    },
]

verification = {
    "assessments": [
        {
            "source_id": 1,
            "stance": "SUPPORTS",
            "reason": "The source discusses AI errors.",
            "quote": "AI systems can generate incorrect",
        },
        {
            "source_id": 2,
            "stance": "SUPPORTS",
            "reason": "The source proves the claim.",
            "quote": "AI always produces false information.",
        },
    ],
    "summary": "Initial assessment",
}

result = validate_evidence(sources, verification)

first = result["assessments"][0]
second = result["assessments"][1]

assert first["stance"] == "SUPPORTS"
assert first["quote_verified"] is True

assert second["stance"] == "INSUFFICIENT"
assert second["quote_verified"] is False

print("SUCCESS: Evidence Validator is working!")
print()

for item in result["assessments"]:
    print("SOURCE:", item["source_id"])
    print("STANCE:", item["stance"])
    print("QUOTE VERIFIED:", item["quote_verified"])
    print()


import json
from types import SimpleNamespace
from backend.verification_agent import _semantic_audit


class FakeCompletions:
    def __init__(self, decisions):
        self.decisions = decisions

    def create(self, **kwargs):
        data = json.loads(kwargs["messages"][1]["content"])
        items = data["evidence_to_audit"]

        audits = [
            {
                "source_id": item["source_id"],
                "decision": self.decisions.get(
                    item["source_id"], "REJECT"
                ),
                "reason": "Offline test decision",
            }
            for item in items
        ]

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=json.dumps({"audits": audits})
                    )
                )
            ]
        )


class FakeClient:
    def __init__(self, decisions):
        self.chat = SimpleNamespace(
            completions=FakeCompletions(decisions)
        )


def run_test(name, decisions, expected_stances):
    claim = (
        "The Sun revolves around the Earth "
        "once every 24 hours."
    )

    evidence = [
        {
            "id": 1,
            "title": "Generic statement",
            "content": (
                "Not everything in the sky "
                "was orbiting Earth."
            ),
        },
        {
            "id": 2,
            "title": "Direct explanation",
            "content": (
                "Earth's rotation causes the Sun's "
                "apparent daily movement across the sky."
            ),
        },
    ]

    assessments = [
        {
            "source_id": 1,
            "stance": "CONTRADICTS",
            "reason": "Proposed contradiction",
            "quote": (
                "Not everything in the sky "
                "was orbiting Earth."
            ),
        },
        {
            "source_id": 2,
            "stance": "CONTRADICTS",
            "reason": "Proposed contradiction",
            "quote": (
                "Earth's rotation causes the Sun's "
                "apparent daily movement across the sky."
            ),
        },
    ]

    result = _semantic_audit(
        FakeClient(decisions),
        claim,
        assessments,
        evidence,
    )

    actual = [item["stance"] for item in result]

    assert actual == expected_stances, (
        f"{name}: expected {expected_stances}, got {actual}"
    )

    print(f"PASS: {name}")


run_test(
    "Reject generic evidence",
    {1: "REJECT", 2: "KEEP"},
    ["INSUFFICIENT", "CONTRADICTS"],
)

run_test(
    "Reject all weak evidence",
    {1: "REJECT", 2: "REJECT"},
    ["INSUFFICIENT", "INSUFFICIENT"],
)

run_test(
    "Missing audit decision is rejected",
    {1: "KEEP"},
    ["CONTRADICTS", "INSUFFICIENT"],
)

print("ALL OFFLINE AUDIT TESTS PASSED")
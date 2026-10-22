
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx


API_URL = "http://127.0.0.1:8000/analyze"

RESULTS_FILE = Path("benchmark_results_v2.json")
SUMMARY_FILE = Path("benchmark_summary_v2.json")

# The backend can take more than a minute because
# it performs research and multiple AI verification calls.
# This is a diagnostic timeout, not a backend fix.
TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=360.0,
    write=30.0,
    pool=10.0,
)

TEST_CASES = [
    {
        "id": "astronomy_true",
        "claim": "The Earth revolves around the Sun.",
        "expected": "PRELIMINARY_SUPPORT",
        "category": "true",
    },
    {
        "id": "astronomy_false",
        "claim": "The Sun revolves around the Earth once every 24 hours.",
        "expected": "PRELIMINARY_CONTRADICTION",
        "category": "false",
    },
    {
        "id": "biology_true",
        "claim": "Humans need oxygen to survive.",
        "expected": "PRELIMINARY_SUPPORT",
        "category": "true",
    },
    {
        "id": "biology_false",
        "claim": (
            "Humans can breathe normally in outer space "
            "without a spacesuit."
        ),
        "expected": "PRELIMINARY_CONTRADICTION",
        "category": "false",
    },
    {
        "id": "science_true",
        "claim": "Water is made of hydrogen and oxygen.",
        "expected": "PRELIMINARY_SUPPORT",
        "category": "true",
    },
    {
        "id": "science_false",
        "claim": "Sound travels faster than light in a vacuum.",
        "expected": "PRELIMINARY_CONTRADICTION",
        "category": "false",
    },
    {
        "id": "technology_true",
        "claim": (
            "Machine learning is a field "
            "of artificial intelligence."
        ),
        "expected": "PRELIMINARY_SUPPORT",
        "category": "true",
    },
    {
        "id": "technology_false",
        "claim": (
            "All artificial intelligence systems "
            "always produce accurate information."
        ),
        "expected": "PRELIMINARY_CONTRADICTION",
        "category": "false",
    },
    {
        "id": "health_absolute",
        "claim": (
            "Drinking coffee is always harmful "
            "to human health."
        ),
        "expected": None,
        "category": "nuanced",
    },
    {
        "id": "health_nuanced",
        "claim": "Eating carbohydrates is always unhealthy.",
        "expected": None,
        "category": "nuanced",
    },
    {
        "id": "technology_nuanced",
        "claim": (
            "Artificial intelligence will replace "
            "every human job."
        ),
        "expected": None,
        "category": "nuanced",
    },
    {
        "id": "context_nuanced",
        "claim": (
            "Remote work always increases "
            "employee productivity."
        ),
        "expected": None,
        "category": "nuanced",
    },
]


def save_json(path, data):
    temporary_path = path.with_name(
        path.name + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temporary_path.replace(path)


def new_result(case):
    return {
        "id": case["id"],
        "category": case["category"],
        "claim": case["claim"],
        "expected": case["expected"],
        "actual": None,
        "passed": None,
        "duration_seconds": None,
        "agents_completed": None,
        "evidence_counts": {},
        "decision_metrics": {},
        "verified_quotes": 0,
        "research_errors": [],
        "evidence": [],
        "http_status": None,
        "error": None,
    }


def run_single_test(client, case):
    result = new_result(case)
    start = time.perf_counter()

    print()
    print("=" * 65)
    print("TEST:", case["id"])
    print("CATEGORY:", case["category"])
    print("CLAIM:", case["claim"])
    print("Sending request...", flush=True)

    try:
        response = client.post(
            API_URL,
            json={"claim": case["claim"]},
        )

        result["http_status"] = response.status_code
        response.raise_for_status()

        data = response.json()
        report = data["report"]

        verdict = report["verdict"]
        expected = case["expected"]

        evidence = report.get("evidence", [])

        verified_quotes = sum(
            item.get("quote_verified") is True
            for item in evidence
        )

        result.update({
            "actual": verdict,
            "passed": (
                verdict == expected
                if expected is not None
                else None
            ),
            "agents_completed": data.get(
                "agents_completed"
            ),
            "evidence_counts": report.get(
                "evidence_counts", {}
            ),
            "decision_metrics": report.get(
                "decision_metrics", {}
            ),
            "verified_quotes": verified_quotes,
            "research_errors": data.get(
                "research_errors", []
            ),
            "evidence": evidence,
        })

        print("VERDICT:", verdict)
        print("EXPECTED:", expected)
        print("PASSED:", result["passed"])
        print("VERIFIED QUOTES:", verified_quotes)
        print(
            "AGENTS COMPLETED:",
            result["agents_completed"],
        )

    except httpx.ReadTimeout as error:
        result["error"] = (
            "ReadTimeout: The backend did not return "
            "a response within the configured read timeout. "
            "Inspect backend logs to identify the slow stage."
        )

        print("READ TIMEOUT:", repr(error))
        print(
            "CHECK: Backend terminal logs for "
            "Planning, Research, Verification, "
            "Evidence Validator, and Decision."
        )

    except httpx.ConnectTimeout as error:
        result["error"] = (
            "ConnectTimeout: Could not connect "
            "to the backend in time."
        )
        print("CONNECT TIMEOUT:", repr(error))

    except httpx.ConnectError as error:
        result["error"] = (
            f"ConnectError: {error}"
        )
        print("CONNECTION ERROR:", repr(error))

    except httpx.HTTPStatusError as error:
        status = error.response.status_code
        result["http_status"] = status
        result["error"] = (
            f"HTTPStatusError: HTTP {status}"
        )

        print("HTTP ERROR:", status)
        print(
            "RESPONSE:",
            error.response.text[:1000],
        )

    except (
        httpx.HTTPError,
        ValueError,
        KeyError,
        TypeError,
    ) as error:
        result["error"] = (
            f"{type(error).__name__}: {error}"
        )

        print("FAILED:", result["error"])

    finally:
        result["duration_seconds"] = round(
            time.perf_counter() - start,
            2,
        )

        if (
            result["error"] is not None
            and case["expected"] is not None
        ):
            result["passed"] = False

        print(
            "DURATION:",
            result["duration_seconds"],
            "seconds",
        )

    return result


def run_benchmark():
    results = []

    print("=" * 65)
    print("VERIFLOW AI - BENCHMARK V2 DIAGNOSTIC")
    print("TOTAL TESTS:", len(TEST_CASES))
    print("READ TIMEOUT:", TIMEOUT.read, "seconds")
    print("=" * 65)

    # Keep the same client for all tests.
    with httpx.Client(timeout=TIMEOUT) as client:
        for index, case in enumerate(TEST_CASES, 1):
            print()
            print(
                f"RUNNING {index}/{len(TEST_CASES)}",
                flush=True,
            )

            result = run_single_test(
                client,
                case,
            )

            results.append(result)

            # Save progress after each test.
            save_json(
                RESULTS_FILE,
                results,
            )

    evaluated = [
        item
        for item in results
        if item["expected"] is not None
    ]

    matched = sum(
        item["passed"] is True
        for item in evaluated
    )

    completed = sum(
        item["error"] is None
        for item in results
    )

    failed_cases = [
        {
            "id": item["id"],
            "error": item["error"],
            "duration_seconds": item[
                "duration_seconds"
            ],
        }
        for item in results
        if item["error"] is not None
    ]

    summary = {
        "benchmark": (
            "VeriFlow AI Benchmark V2 Diagnostic"
        ),
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_tests": len(TEST_CASES),
        "completed": completed,
        "evaluated_tests": len(evaluated),
        "matched_expected": matched,
        "match_rate": (
            round(
                matched / len(evaluated),
                3,
            )
            if evaluated
            else None
        ),
        "failed_cases": failed_cases,
        "note": (
            "Expected verdicts are preliminary test "
            "targets, not independently verified "
            "ground-truth labels. Exact quotation "
            "matching does not prove semantic accuracy."
        ),
    }

    save_json(
        SUMMARY_FILE,
        summary,
    )

    print()
    print("=" * 65)
    print("BENCHMARK V2 DIAGNOSTIC COMPLETED")
    print("TOTAL TESTS:", len(TEST_CASES))
    print("COMPLETED:", completed)
    print(
        "EXPECTED VERDICTS MATCHED:",
        f"{matched}/{len(evaluated)}",
    )
    print("FAILED REQUESTS:", len(failed_cases))
    print("RESULTS:", RESULTS_FILE)
    print("SUMMARY:", SUMMARY_FILE)
    print("=" * 65)


if __name__ == "__main__":
    run_benchmark()


from collections import Counter
from urllib.parse import urlparse
import re


ALLOWED_STANCES = {
    "SUPPORTS",
    "CONTRADICTS",
    "INSUFFICIENT",
}

MIN_DECISIVE_SOURCES = 2
DECISION_THRESHOLD = 0.75

ABSOLUTE_TERMS = {
    "always",
    "never",
    "every",
    "all",
    "none",
    "without exception",
    "in every case",
}


def _get_domain(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""

    try:
        domain = urlparse(url).hostname or ""
        domain = domain.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except ValueError:
        return ""


def _is_absolute_claim(claim: str) -> bool:
    normalized = claim.lower()

    for term in ABSOLUTE_TERMS:
        pattern = r"\b" + re.escape(term) + r"\b"

        if re.search(pattern, normalized):
            return True

    return False


def make_decision(
    claim: str,
    sources: list[dict],
    verification: dict,
) -> dict:

    assessments = verification.get("assessments", [])

    source_lookup = {
        source["id"]: source
        for source in sources
    }

    valid_assessments = []
    seen_ids = set()

    for item in assessments:
        if not isinstance(item, dict):
            continue

        source_id = item.get("source_id")

        if source_id not in source_lookup:
            continue

        if source_id in seen_ids:
            continue

        stance = item.get("stance")

        if stance not in ALLOWED_STANCES:
            continue

        seen_ids.add(source_id)

        if (
            stance in {"SUPPORTS", "CONTRADICTS"}
            and item.get("quote_verified") is not True
        ):
            item = {
                **item,
                "stance": "INSUFFICIENT",
                "reason": (
                    "No verified quotation is available "
                    "for this classification."
                ),
                "quote": "",
            }

        valid_assessments.append(item)

    counts = Counter(
        item["stance"]
        for item in valid_assessments
    )

    supports = counts["SUPPORTS"]
    contradicts = counts["CONTRADICTS"]
    insufficient = counts["INSUFFICIENT"]

    decisive_total = supports + contradicts

    if decisive_total > 0:
        support_ratio = supports / decisive_total
        contradiction_ratio = contradicts / decisive_total
    else:
        support_ratio = 0.0
        contradiction_ratio = 0.0

    absolute_claim = _is_absolute_claim(claim)

    supporting_domains = set()
    contradicting_domains = set()
    all_domains = set()

    evidence_report = []

    for item in valid_assessments:
        source = source_lookup[item["source_id"]]

        url = source.get("url", "")
        domain = _get_domain(url)

        if domain:
            all_domains.add(domain)

        stance = item["stance"]

        if stance == "SUPPORTS" and domain:
            supporting_domains.add(domain)

        elif stance == "CONTRADICTS" and domain:
            contradicting_domains.add(domain)

        evidence_report.append({
            "source_id": item["source_id"],
            "title": source.get("title", ""),
            "url": url,
            "stance": stance,
            "reason": item.get("reason", ""),
            "quote": item.get("quote", ""),
            "quote_verified": item.get(
                "quote_verified",
                False,
            ),
        })

    support_domain_count = len(supporting_domains)
    contradiction_domain_count = len(contradicting_domains)

    decision_reason = ""

    if decisive_total == 0:
        verdict = "INSUFFICIENT_EVIDENCE"
        decision_reason = (
            "No verified decisive evidence was available."
        )

    elif supports > 0 and contradicts > 0:
        verdict = "CONFLICTING_EVIDENCE"
        decision_reason = (
            "Verified evidence includes both supporting "
            "and contradicting assessments."
        )

    elif supports > 0:
        if (
            supports >= MIN_DECISIVE_SOURCES
            and support_domain_count >= MIN_DECISIVE_SOURCES
            and support_ratio >= DECISION_THRESHOLD
            and not absolute_claim
        ):
            verdict = "PRELIMINARY_SUPPORT"
            decision_reason = (
                "At least two sources from different domains "
                "provide verified supporting quotations. "
                "This remains a preliminary assessment."
            )

        else:
            verdict = "INSUFFICIENT_EVIDENCE"

            if absolute_claim:
                decision_reason = (
                    "The claim contains absolute wording. "
                    "The available snippet-based evidence "
                    "does not establish that the claim holds "
                    "without exceptions."
                )
            else:
                decision_reason = (
                    "Supporting evidence does not meet the "
                    "minimum source and domain requirements."
                )

    else:
        if (
            contradicts >= MIN_DECISIVE_SOURCES
            and contradiction_domain_count >= MIN_DECISIVE_SOURCES
            and contradiction_ratio >= DECISION_THRESHOLD
        ):
            verdict = "PRELIMINARY_CONTRADICTION"
            decision_reason = (
                "At least two sources from different domains "
                "provide verified contradicting quotations. "
                "This remains a preliminary assessment."
            )

        else:
            verdict = "INSUFFICIENT_EVIDENCE"
            decision_reason = (
                "Contradicting evidence does not meet the "
                "minimum source and domain requirements."
            )

    return {
        "claim": claim,
        "verdict": verdict,
        "evidence_counts": {
            "supports": supports,
            "contradicts": contradicts,
            "insufficient": insufficient,
        },
        "decision_metrics": {
            "decisive_sources": decisive_total,
            "support_ratio": round(support_ratio, 3),
            "contradiction_ratio": round(
                contradiction_ratio,
                3,
            ),
            "unique_domains": len(all_domains),
            "supporting_domains": support_domain_count,
            "contradicting_domains": contradiction_domain_count,
            "absolute_claim": absolute_claim,
        },
        "decision_reason": decision_reason,
        "summary": verification.get("summary", ""),
        "evidence": evidence_report,
        "limitations": [
            "This is a preliminary AI-assisted assessment.",
            "A verified quotation only confirms that text "
            "appears in a retrieved snippet.",
            "It does not establish that the source is "
            "accurate or that the quotation proves the claim.",
            "The decision threshold and minimum source "
            "requirements are heuristics, not calibrated "
            "confidence scores.",
            "Different domains do not guarantee independent "
            "underlying evidence.",
            "Absolute claims require special caution because "
            "limited observations cannot establish that "
            "something holds without exceptions.",
            "Full source documents have not been "
            "independently verified.",
        ],
        "human_review_recommended": True,
        "evidence_verified": False,
    }

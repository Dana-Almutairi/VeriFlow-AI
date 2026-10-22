
def validate_evidence(
    sources: list[dict],
    verification: dict,
) -> dict:
    """
    Validate evidence assessments against retrieved sources.

    Decisive assessments require an exact quotation
    from the corresponding source content.
    """

    if not isinstance(sources, list):
        raise ValueError("Sources must be a list")

    if not isinstance(verification, dict):
        raise ValueError("Verification must be a dictionary")

    source_lookup = {}

    for source in sources:
        if not isinstance(source, dict):
            continue

        source_id = source.get("id")

        if type(source_id) is not int:
            continue

        if source_id in source_lookup:
            continue

        source_lookup[source_id] = source

    validated_assessments = []
    processed_ids = set()

    assessments = verification.get("assessments", [])

    if not isinstance(assessments, list):
        raise ValueError("Assessments must be a list")

    for assessment in assessments:
        if not isinstance(assessment, dict):
            continue

        source_id = assessment.get("source_id")

        if type(source_id) is not int:
            continue

        if source_id in processed_ids:
            continue

        source = source_lookup.get(source_id)

        if source is None:
            continue

        processed_ids.add(source_id)

        stance = assessment.get(
            "stance",
            "INSUFFICIENT",
        )

        reason = assessment.get("reason", "")
        quote = assessment.get("quote", "")

        content = source.get("content", "")

        if not isinstance(content, str):
            content = ""

        if not isinstance(reason, str):
            reason = ""

        if not isinstance(quote, str):
            quote = ""

        quote = quote.strip()

        quote_valid = (
            bool(quote)
            and quote in content
        )

        if stance not in {
            "SUPPORTS",
            "CONTRADICTS",
            "INSUFFICIENT",
        }:
            stance = "INSUFFICIENT"
            reason = "Invalid evidence stance."

        if stance in {"SUPPORTS", "CONTRADICTS"}:
            if not quote_valid:
                stance = "INSUFFICIENT"
                reason = (
                    "No verifiable quotation was "
                    "provided from the retrieved source."
                )

        if stance == "INSUFFICIENT":
            quote = ""
            quote_valid = False

        validated_assessments.append({
            "source_id": source_id,
            "stance": stance,
            "reason": reason,
            "quote": quote,
            "quote_verified": quote_valid,
        })

    supports = sum(
        item["stance"] == "SUPPORTS"
        for item in validated_assessments
    )

    contradicts = sum(
        item["stance"] == "CONTRADICTS"
        for item in validated_assessments
    )

    insufficient = sum(
        item["stance"] == "INSUFFICIENT"
        for item in validated_assessments
    )

    summary = {
        "total_sources": len(validated_assessments),
        "supports": supports,
        "contradicts": contradicts,
        "insufficient": insufficient,
    }

    return {
        "assessments": validated_assessments,
        "summary": summary,
        "validation_method": "exact_snippet_match",
    }

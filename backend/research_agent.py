
import os
import re
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv(override=True)


STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were",
    "of", "to", "in", "on", "for", "and", "or",
    "with", "that", "this", "does", "do", "did",
    "when", "where", "what", "why", "how",
    "evidence", "fact", "check", "scientific",
    "research", "study", "official",
}

TRUSTED_DOMAIN_SUFFIXES = (
    ".gov",
    ".edu",
    ".ac.uk",
)

TRUSTED_DOMAINS = {
    "nasa.gov",
    "esa.int",
    "who.int",
    "cdc.gov",
    "nih.gov",
    "nature.com",
    "science.org",
    "britannica.com",
}

MAX_QUERIES = 3
MAX_RESULTS_PER_QUERY = 8
MAX_SELECTED_SOURCES = 10
MAX_CONTENT_CHARS = 1500
MAX_SOURCES_PER_DOMAIN = 2


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())

    return urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path.rstrip("/") or "/",
        "",
        "",
    ))


def get_hostname(url: str) -> str:
    return (
        urlsplit(url).hostname or ""
    ).lower().removeprefix("www.")


def extract_keywords(text: str) -> set[str]:
    words = re.findall(
        r"[a-zA-Z0-9]+",
        text.lower(),
    )

    return {
        word
        for word in words
        if len(word) > 2
        and word not in STOP_WORDS
    }


def is_trusted_domain(url: str) -> bool:
    hostname = get_hostname(url)

    if not hostname:
        return False

    if hostname.endswith(TRUSTED_DOMAIN_SUFFIXES):
        return True

    return any(
        hostname == domain
        or hostname.endswith("." + domain)
        for domain in TRUSTED_DOMAINS
    )


def calculate_relevance(
    query: str,
    title: str,
    content: str,
) -> float:
    query_words = extract_keywords(query)

    if not query_words:
        return 0.0

    title_words = extract_keywords(title)
    content_words = extract_keywords(content)

    title_overlap = (
        len(query_words.intersection(title_words))
        / len(query_words)
    )

    content_overlap = (
        len(query_words.intersection(content_words))
        / len(query_words)
    )

    return round(
        title_overlap * 0.4
        + content_overlap * 0.6,
        4,
    )


def calculate_quality_score(
    query: str,
    result: dict,
) -> float:
    title = result.get("title") or ""
    content = result.get("content") or ""
    url = result.get("url") or ""

    relevance = calculate_relevance(
        query,
        title,
        content,
    )

    score = relevance * 0.65

    if is_trusted_domain(url):
        score += 0.20

    if len(content.strip()) >= 150:
        score += 0.10

    if len(content.strip()) >= 400:
        score += 0.05

    return round(
        min(score, 1.0),
        4,
    )


def normalize_query(query: str) -> str:
    return " ".join(query.lower().split())


def prepare_queries(
    queries: list[str],
) -> list[str]:
    """
    Preserve the Planning Agent's research intent.

    Remove duplicate queries without replacing them
    with predetermined facts or expected verdicts.
    """

    prepared = []
    seen = set()

    for query in queries:
        if not isinstance(query, str):
            continue

        query = query.strip()

        if not query:
            continue

        normalized = normalize_query(query)

        if normalized in seen:
            continue

        seen.add(normalized)
        prepared.append(query)

        if len(prepared) >= MAX_QUERIES:
            break

    return prepared


def select_diverse_sources(
    candidates: list[dict],
) -> list[dict]:
    """
    Prefer strong results from different websites.

    Avoid allowing one website to dominate
    the entire evidence set.
    """

    ranked = sorted(
        candidates,
        key=lambda item: item["quality_score"],
        reverse=True,
    )

    selected = []
    domain_counts = {}
    used_urls = set()

    for candidate in ranked:
        if len(selected) >= MAX_SELECTED_SOURCES:
            break

        url = candidate["url"]
        normalized_url = normalize_url(url)
        hostname = get_hostname(url)

        if normalized_url in used_urls:
            continue

        if not hostname:
            continue

        if (
            domain_counts.get(hostname, 0)
            >= MAX_SOURCES_PER_DOMAIN
        ):
            continue

        selected.append(candidate)
        used_urls.add(normalized_url)

        domain_counts[hostname] = (
            domain_counts.get(hostname, 0) + 1
        )

    return selected


def research_claim(
    queries: list[str],
) -> dict:
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Tavily API key is missing"
        )

    prepared_queries = prepare_queries(queries)

    if not prepared_queries:
        raise ValueError(
            "No research queries provided"
        )

    client = TavilyClient(
        api_key=api_key
    )

    candidates = []
    seen_urls = set()
    search_log = []
    errors = []

    for query in prepared_queries:
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=MAX_RESULTS_PER_QUERY,
            )

            results = response.get(
                "results",
                [],
            )

            search_log.append({
                "query": query,
                "results_found": len(results),
            })

            for result in results:
                if not isinstance(result, dict):
                    continue

                url = result.get("url") or ""
                title = result.get("title") or ""
                content = result.get("content") or ""

                if not isinstance(url, str):
                    continue

                if not isinstance(title, str):
                    title = ""

                if not isinstance(content, str):
                    continue

                if not url.startswith(
                    ("https://", "http://")
                ):
                    continue

                if not content.strip():
                    continue

                normalized = normalize_url(url)

                if normalized in seen_urls:
                    continue

                seen_urls.add(normalized)

                quality_score = calculate_quality_score(
                    query,
                    result,
                )

                candidates.append({
                    "title": title,
                    "url": url,
                    "content": content[
                        :MAX_CONTENT_CHARS
                    ],
                    "search_query": query,
                    "quality_score": quality_score,
                })

        except Exception as error:
            errors.append({
                "query": query,
                "error_type": type(error).__name__,
            })

    selected = select_diverse_sources(
        candidates
    )

    sources = []

    for index, candidate in enumerate(
        selected,
        start=1,
    ):
        sources.append({
            "id": index,
            "title": candidate["title"],
            "url": candidate["url"],
            "content": candidate["content"],
            "search_query": candidate["search_query"],
            "quality_score": candidate["quality_score"],
        })

    return {
        "sources": sources,
        "search_log": search_log,
        "errors": errors,
        "total_sources": len(sources),
    }

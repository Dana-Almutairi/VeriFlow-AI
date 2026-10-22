
import json
import time

import httpx


URL = "http://127.0.0.1:8000/analyze/stream"

CLAIM = (
    "Remote work always increases "
    "employee productivity."
)


def main():
    print("\nVERIFLOW AI - TIMEOUT DIAGNOSTIC")
    print("CLAIM:", CLAIM)
    print("-" * 55, flush=True)

    start = time.perf_counter()
    last_agent = "Not started"

    timeout = httpx.Timeout(
        connect=15.0,
        read=300.0,
        write=15.0,
        pool=15.0,
    )

    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream(
                "POST",
                URL,
                json={"claim": CLAIM},
            ) as response:
                response.raise_for_status()

                event_name = None

                for line in response.iter_lines():
                    if not line:
                        continue

                    if line.startswith("event:"):
                        event_name = line[6:].strip()
                        continue

                    if not line.startswith("data:"):
                        continue

                    raw_data = line[5:].strip()

                    try:
                        data = json.loads(raw_data)
                    except json.JSONDecodeError:
                        data = {"raw": raw_data[:300]}

                    elapsed = round(
                        time.perf_counter() - start,
                        2,
                    )

                    if event_name == "agent_started":
                        last_agent = str(data.get(
                            "agent",
                            data.get("name", "Unknown"),
                        ))

                    print(
                        f"[{elapsed}s] "
                        f"EVENT: {event_name} | "
                        f"DATA: {str(data)[:400]}",
                        flush=True,
                    )

                    if event_name in {
                        "analysis_completed",
                        "analysis_error",
                    }:
                        break

                    event_name = None

    except httpx.HTTPError as error:
        print(
            "\nNETWORK ERROR:",
            type(error).__name__,
            str(error),
        )

    finally:
        duration = round(
            time.perf_counter() - start,
            2,
        )

        print("\nLAST STARTED AGENT:", last_agent)
        print("TOTAL DURATION:", duration, "seconds")


if __name__ == "__main__":
    main()


import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

WINDOW_SECONDS = 3600
MAX_REQUESTS = int(os.getenv("MAX_ANALYSES_PER_HOUR", "3"))
MAX_GLOBAL_REQUESTS = int(os.getenv("MAX_GLOBAL_ANALYSES_PER_HOUR", "10"))

_lock = threading.Lock()
_requests = defaultdict(deque)
_global_requests = deque()


def check_analysis_limit(request: Request):
    # Use the connecting client's address.
    # Do not trust arbitrary X-Forwarded-For headers.
    client_ip = request.client.host if request.client else "unknown"

    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS

    with _lock:
        user_requests = _requests[client_ip]

        while user_requests and user_requests[0] <= cutoff:
            user_requests.popleft()

        while _global_requests and _global_requests[0] <= cutoff:
            _global_requests.popleft()

        if len(user_requests) >= MAX_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail="Analysis limit reached. Please try again later.",
                headers={"Retry-After": "3600"},
            )

        if len(_global_requests) >= MAX_GLOBAL_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail="Demo usage limit reached. Please try again later.",
                headers={"Retry-After": "3600"},
            )

        user_requests.append(now)
        _global_requests.append(now)

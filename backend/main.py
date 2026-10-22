
import os
import logging
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.types import ASGIApp, Receive, Scope, Send, Message
from fastapi import Request
from backend.rate_limiter import check_analysis_limit
from backend.planning_agent import plan_research
from backend.research_agent import research_claim
from backend.verification_agent import verify_evidence
from backend.evidence_validator import validate_evidence
from backend.decision_agent import make_decision
from backend.streaming import router as streaming_router
from backend.pdf_generator import generate_pdf_report


load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("veriflow")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

MAX_REQUEST_BYTES = 100_000
MAX_PDF_REQUEST_BYTES = 500_000

VERSION = "0.6.0"


class RequestBodyTooLarge(Exception):
    pass


class RequestSecurityMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")

        max_size = (
            MAX_PDF_REQUEST_BYTES
            if path == "/report/pdf"
            else MAX_REQUEST_BYTES
        )

        headers = {
            key.lower(): value
            for key, value in scope.get("headers", [])
        }

        async def secure_send(message: Message):
            if message["type"] == "http.response.start":
                response_headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() not in {
                        b"x-content-type-options",
                        b"x-frame-options",
                        b"referrer-policy",
                        b"permissions-policy",
                    }
                ]

                response_headers.extend([
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                    (
                        b"permissions-policy",
                        b"camera=(), microphone=(), geolocation=()",
                    ),
                ])

                message["headers"] = response_headers

            await send(message)

        async def reject(status_code: int, detail: str):
            response = Response(
                content=detail,
                status_code=status_code,
            )
            await response(scope, receive, secure_send)

        if method not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, secure_send)
            return

        raw_length = headers.get(b"content-length")

        if raw_length is not None:
            try:
                declared_size = int(raw_length)
            except ValueError:
                await reject(400, "Invalid Content-Length")
                return

            if declared_size < 0:
                await reject(400, "Invalid Content-Length")
                return

            if declared_size > max_size:
                await reject(413, "Request body too large")
                return

        # Buffer the bounded request body before calling FastAPI.
        # This avoids consuming the body twice or breaking SSE.
        body = bytearray()

        while True:
            message = await receive()

            if message["type"] == "http.disconnect":
                return

            if message["type"] != "http.request":
                continue

            body.extend(message.get("body", b""))

            if len(body) > max_size:
                await reject(413, "Request body too large")
                return

            if not message.get("more_body", False):
                break

        cached_body = bytes(body)
        body_delivered = False

        async def replay_receive() -> Message:
            nonlocal body_delivered

            if not body_delivered:
                body_delivered = True

                return {
                    "type": "http.request",
                    "body": cached_body,
                    "more_body": False,
                }

            # Preserve real disconnect events for streaming routes.
            return await receive()

        await self.app(
            scope,
            replay_receive,
            secure_send,
        )


app = FastAPI(
    title="VeriFlow AI",
    description="Multi-agent evidence analysis system",
    version=VERSION,
)

app.add_middleware(RequestSecurityMiddleware)
app.include_router(streaming_router)

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static",
)


class ClaimRequest(BaseModel):
    claim: str = Field(
        min_length=5,
        max_length=2000,
        description="The factual claim to investigate",
    )

    @field_validator("claim")
    @classmethod
    def validate_claim(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 5:
            raise ValueError(
                "Claim must contain at least 5 characters"
            )

        if not any(char.isalnum() for char in value):
            raise ValueError(
                "Claim must contain readable text"
            )

        return value


class PDFReportRequest(BaseModel):
    report: dict[str, Any]


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


@app.get("/style.css", include_in_schema=False)
def frontend_css():
    return FileResponse(
        FRONTEND_DIR / "style.css",
        media_type="text/css",
    )


@app.get("/script.js", include_in_schema=False)
def frontend_javascript():
    return FileResponse(
        FRONTEND_DIR / "script.js",
        media_type="application/javascript",
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "application": "VeriFlow AI",
        "version": VERSION,
        "agents": [
            "Planning Agent",
            "Research Agent",
            "Verification Agent",
            "Evidence Validator",
            "Decision Agent",
        ],
    }


def check_api_keys():
    if not os.getenv("NEBIUS_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Analysis service unavailable",
        )

    if not os.getenv("TAVILY_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Analysis service unavailable",
        )


def execute_agent(agent_name, function, *args):
    started_at = time.perf_counter()

    try:
        result = function(*args)

        duration = round(
            time.perf_counter() - started_at,
            2,
        )

        logger.info(
            "%s completed in %.2fs",
            agent_name,
            duration,
        )

        return result, duration

    except Exception as error:
        logger.exception(
            "%s failed",
            agent_name,
        )

        raise HTTPException(
            status_code=502,
            detail=f"{agent_name} failed",
        ) from error


@app.post("/analyze")
def analyze_claim(request: ClaimRequest, http_request: Request):
    check_api_keys()
    check_analysis_limit(http_request)

    analysis_start = time.perf_counter()
    agent_steps = []

    plan, duration = execute_agent(
        "Planning Agent",
        plan_research,
        request.claim,
    )

    agent_steps.append({
        "agent": "Planning Agent",
        "status": "completed",
        "duration_seconds": duration,
        "output": plan,
    })

    research, duration = execute_agent(
        "Research Agent",
        research_claim,
        plan["queries"],
    )

    agent_steps.append({
        "agent": "Research Agent",
        "status": "completed",
        "duration_seconds": duration,
        "output": {
            "total_sources": research["total_sources"],
            "search_log": research["search_log"],
            "errors": research["errors"],
        },
    })

    verification, duration = execute_agent(
        "Verification Agent",
        verify_evidence,
        request.claim,
        research["sources"],
    )

    agent_steps.append({
        "agent": "Verification Agent",
        "status": "completed",
        "duration_seconds": duration,
        "output": {
            "assessments": len(
                verification["assessments"]
            ),
            "summary": verification["summary"],
        },
    })

    validated, duration = execute_agent(
        "Evidence Validator",
        validate_evidence,
        research["sources"],
        verification,
    )

    verified_quotes = sum(
        item.get("quote_verified") is True
        for item in validated["assessments"]
    )

    agent_steps.append({
        "agent": "Evidence Validator",
        "status": "completed",
        "duration_seconds": duration,
        "output": {
            "total_assessments": len(
                validated["assessments"]
            ),
            "verified_quotes": verified_quotes,
        },
    })

    report, duration = execute_agent(
        "Decision Agent",
        make_decision,
        request.claim,
        research["sources"],
        validated,
    )

    agent_steps.append({
        "agent": "Decision Agent",
        "status": "completed",
        "duration_seconds": duration,
        "output": {
            "verdict": report["verdict"],
            "evidence_counts": report["evidence_counts"],
        },
    })

    report["validation"] = {
        "method": "exact_snippet_match",
        "verified_quotes": verified_quotes,
        "total_assessments": len(
            validated["assessments"]
        ),
    }

    return {
        "application": "VeriFlow AI",
        "version": VERSION,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "report": report,
        "research_plan": plan,
        "research_errors": research["errors"],
        "agent_steps": agent_steps,
        "agents_completed": len(agent_steps),
        "total_duration_seconds": round(
            time.perf_counter() - analysis_start,
            2,
        ),
    }


@app.post("/report/pdf")
def download_pdf(request: PDFReportRequest):
    report = request.report
    claim = report.get("claim")

    if not isinstance(claim, str):
        raise HTTPException(
            status_code=422,
            detail="Invalid report: missing claim",
        )

    if len(claim) > 2000:
        raise HTTPException(
            status_code=422,
            detail="Invalid report: claim too long",
        )

    try:
        pdf_content = generate_pdf_report(report)

    except Exception as error:
        logger.exception("PDF generation failed")

        raise HTTPException(
            status_code=500,
            detail="Could not generate PDF report",
        ) from error

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                'attachment; filename="VeriFlow_AI_Report.pdf"',
            "Cache-Control": "no-store",
        },
    )

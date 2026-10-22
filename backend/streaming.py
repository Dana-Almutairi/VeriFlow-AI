
import json
import logging
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.planning_agent import plan_research
from backend.research_agent import research_claim
from backend.verification_agent import verify_evidence
from backend.evidence_validator import validate_evidence
from backend.decision_agent import make_decision

logger = logging.getLogger("veriflow")
router = APIRouter()


class StreamClaimRequest(BaseModel):
    claim: str = Field(min_length=5, max_length=2000)


def send_event(event_type: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


def run_streaming_analysis(claim: str):
    steps = []
    started_at = time.perf_counter()
    agent_started_at = None
    current_agent = None

    agents = [
        "Planning Agent",
        "Research Agent",
        "Verification Agent",
        "Evidence Validator",
        "Decision Agent",
    ]

    try:
        yield send_event("pipeline_started", {
            "agents": agents,
            "total_agents": len(agents),
        })

        # STEP 1: PLANNING
        current_agent = agents[0]
        agent_started_at = time.perf_counter()

        yield send_event("agent_started", {
            "agent": current_agent,
            "step": 1,
        })

        plan = plan_research(claim)

        duration = round(
            time.perf_counter() - agent_started_at, 2
        )

        steps.append({
            "agent": current_agent,
            "status": "completed",
            "duration_seconds": duration,
        })

        logger.info(
            "%s completed in %.2fs",
            current_agent,
            duration,
        )

        yield send_event("agent_completed", {
            "agent": current_agent,
            "step": 1,
            "duration_seconds": duration,
        })

        # STEP 2: RESEARCH
        current_agent = agents[1]
        agent_started_at = time.perf_counter()

        yield send_event("agent_started", {
            "agent": current_agent,
            "step": 2,
        })

        research = research_claim(plan["queries"])

        duration = round(
            time.perf_counter() - agent_started_at, 2
        )

        steps.append({
            "agent": current_agent,
            "status": "completed",
            "duration_seconds": duration,
        })

        logger.info(
            "%s completed in %.2fs",
            current_agent,
            duration,
        )

        yield send_event("agent_completed", {
            "agent": current_agent,
            "step": 2,
            "total_sources": research["total_sources"],
            "duration_seconds": duration,
        })

        # STEP 3: VERIFICATION
        current_agent = agents[2]
        agent_started_at = time.perf_counter()

        yield send_event("agent_started", {
            "agent": current_agent,
            "step": 3,
        })

        verification = verify_evidence(
            claim,
            research["sources"],
        )

        duration = round(
            time.perf_counter() - agent_started_at, 2
        )

        steps.append({
            "agent": current_agent,
            "status": "completed",
            "duration_seconds": duration,
        })

        logger.info(
            "%s completed in %.2fs",
            current_agent,
            duration,
        )

        yield send_event("agent_completed", {
            "agent": current_agent,
            "step": 3,
            "assessments": len(
                verification["assessments"]
            ),
            "duration_seconds": duration,
        })

        # STEP 4: EVIDENCE VALIDATION
        current_agent = agents[3]
        agent_started_at = time.perf_counter()

        yield send_event("agent_started", {
            "agent": current_agent,
            "step": 4,
        })

        validated = validate_evidence(
            research["sources"],
            verification,
        )

        verified_quotes = sum(
            item.get("quote_verified") is True
            for item in validated["assessments"]
        )

        duration = round(
            time.perf_counter() - agent_started_at, 2
        )

        steps.append({
            "agent": current_agent,
            "status": "completed",
            "duration_seconds": duration,
        })

        logger.info(
            "%s completed in %.2fs",
            current_agent,
            duration,
        )

        yield send_event("agent_completed", {
            "agent": current_agent,
            "step": 4,
            "verified_quotes": verified_quotes,
            "duration_seconds": duration,
        })

        # STEP 5: DECISION
        current_agent = agents[4]
        agent_started_at = time.perf_counter()

        yield send_event("agent_started", {
            "agent": current_agent,
            "step": 5,
        })

        report = make_decision(
            claim,
            research["sources"],
            validated,
        )

        report["validation"] = {
            "method": "exact_snippet_match",
            "verified_quotes": verified_quotes,
            "total_assessments": len(
                validated["assessments"]
            ),
        }

        duration = round(
            time.perf_counter() - agent_started_at, 2
        )

        steps.append({
            "agent": current_agent,
            "status": "completed",
            "duration_seconds": duration,
        })

        logger.info(
            "%s completed in %.2fs",
            current_agent,
            duration,
        )

        yield send_event("agent_completed", {
            "agent": current_agent,
            "step": 5,
            "duration_seconds": duration,
        })

        total_duration = round(
            time.perf_counter() - started_at, 2
        )

        logger.info(
            "Pipeline completed in %.2fs",
            total_duration,
        )

        yield send_event("analysis_completed", {
            "application": "VeriFlow AI",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "report": report,
            "research_plan": plan,
            "research_errors": research["errors"],
            "agent_steps": steps,
            "agents_completed": len(steps),
            "total_duration_seconds": total_duration,
        })

    except Exception:
        total_duration = round(
            time.perf_counter() - started_at, 2
        )

        agent_duration = (
            round(time.perf_counter() - agent_started_at, 2)
            if agent_started_at is not None
            else 0.0
        )

        logger.exception(
            "Pipeline failed | agent=%s | "
            "agent_duration=%.2fs | total=%.2fs",
            current_agent,
            agent_duration,
            total_duration,
        )

        yield send_event("analysis_error", {
            "message": "Analysis failed. Please try again.",
            "failed_agent": current_agent,
            "completed_agents": len(steps),
            "total_duration_seconds": total_duration,
        })


@router.post("/analyze/stream")
def analyze_stream(request: StreamClaimRequest):
    if not os.getenv("NEBIUS_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="Nebius API key is not configured",
        )

    if not os.getenv("TAVILY_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="Tavily API key is not configured",
        )

    return StreamingResponse(
        run_streaming_analysis(request.claim),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
from services.Gemini_Service import get_decision
from services.Servicenow_Service import update_incident
import logging
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("task0")

app = FastAPI(title="Agentic Incident Flow")

processed_incidents: set[str] = set() # If the same incident id arrives twice, we only process it once

class IncidentPayload(BaseModel):
    incident_sys_id: str
    number: str
    short_description: str
    description: str | None = None # Since description is optional
    priority: int


@app.post("/webhook", status_code=202)

async def webhook(payload: IncidentPayload, background_tasks: BackgroundTasks):
    if payload.incident_sys_id in processed_incidents:
        # Already handled this exact incident before skip it
        logger.info("Duplicate incident ignored ", payload.number)
        return {"status": "duplicate_ignored", "number": payload.number}
    
    processed_incidents.add(payload.incident_sys_id)
    background_tasks.add_task(process_incident, payload)

    logger.info("Accepted incident %s, processing in background.", payload.number)
    return {"status": "accepted", "number": payload.number}


async def process_incident(payload: IncidentPayload) -> None:
    try:
        decision, message = await get_decision(
            short_description=payload.short_description,
            description=payload.description,
        )
        logger.info("Decision for %s: %s | %s", payload.number, decision, message)
        await update_incident(
            sys_id=payload.incident_sys_id,
            decision=decision,
            message=message,
        )
        logger.info(
            "Incident %s processed successfully -> decision=%s",
            payload.number, decision,
        )

    except Exception as exc:
        logger.error("Failed to process incident %s: %s", payload.number, exc)

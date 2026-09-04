# Write the decission of AI back into the ServiceNow incident

import os
import logging
import httpx
logger = logging.getLogger("task0")

SN_INSTANCE_URL = os.environ["servicenow_url"].rstrip("/")   
SN_USER = os.environ["servicenow_user"]          
SN_PASS = os.environ["servicenow_pass"]

# print("--- DEBUG ---")
# print(f"USER SEEN BY PYTHON: >{SN_USER}<")
# print(f"PASS SEEN BY PYTHON: >{SN_PASS}<")

async def update_incident(sys_id: str, decision: str, message: str) -> None:

    url = f"{SN_INSTANCE_URL}/api/now/table/incident/{sys_id}"

    if decision == "respond":
        body = {
            "work_notes": f"Automated resolution: {message}",
            "close_notes": message,
            "state": "6",  
            "close_code": "Solved (Permanently)",
        }
    elif decision == "ask":
        body = {"comments": message}
    else:  # "escalate"
        body = {"work_notes": f"Escalated by automated triage: {message}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.patch(
            url,
            auth=(SN_USER, SN_PASS),
            json=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        # Raises an exception for any 4xx/5xx response
        response.raise_for_status()

    logger.info("Updated incident %s in ServiceNow (decision=%s).", sys_id, decision)
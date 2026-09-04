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
    print(f"### ENTER update_incident sys_id={sys_id} decision={decision} url={url}")

    if decision == "respond":
        body = {
            "work_notes": message,
            "state": "6",
            "close_notes": message,
            "close_code": "Resolved by caller"
        }
    elif decision == "ask":
        body = {"comments": message}
    else:
        body = {"work_notes": f"Escalated by automated triage: {message}"}

    print(f"### BODY BUILT: {body}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        print("### CALLING client.patch NOW")
        response = await client.patch(
            url, auth=(SN_USER, SN_PASS), json=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        print(f"### GOT RESPONSE {response.status_code}: {response.text}")
        response.raise_for_status()

    logger.info("Updated incident %s in ServiceNow (decision=%s).", sys_id, decision)
    print("### EXIT update_incident normally")
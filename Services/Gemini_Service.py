import os
import json
import logging
from google import genai
from dotenv import load_dotenv
logger = logging.getLogger("task0")
load_dotenv()

client = genai.Client(api_key=os.environ["gemini_api"]) # 1- uploading the API key for gemini
# 2-loading the five knowledge base articles
_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "AI_Engineering_Task0_Assets", "kb_articles.json")
with open(_KB_PATH, "r") as f:
    kb_articles = json.load(f)["articles"]

def build_prompt(short_description: str, description: str) -> str: # this function is used to commit the prompt to Gemini

    articles_block = "\n".join(f"{a['id']}. {a['text']}" for a in kb_articles)
    return f"""You are an IT support triage assistant. You must decide what to do with a support ticket using 
    ONLY the knowledge base articles below. Do not use any outside knowledge, and do not guess at fixes that 
    are not explicitly listed here. KNOWLEDGE BASE ARTICLES:
{articles_block}
TICKET:
Short description: {short_description}
Description: {description if description else "(no further detail provided)"}
Decide exactly one of the following:
- "respond": one of the articles above clearly and directly solves this problem.
- "ask": an article might apply, but the ticket is too vague to be sure —
  you need more detail from the customer before you can help.
- "escalate": none of the articles above cover this problem at all, so a
  human must handle it.

Reply with ONLY valid JSON — no markdown formatting, no code fences, no
explanation text before or after — in exactly this shape:
{{"decision": "respond" | "ask" | "escalate", "message": "a short, clear message"}}

If you decide "respond", the message should be the fix instructions.
If you decide "ask", the message should be the clarifying question to send
the customer.
If you decide "escalate", the message should briefly explain why."""


async def get_decision(short_description: str, description: str) -> tuple[str, str]: 
    """
    Calls Gemini and returns (decision, message).
    If Gemini's reply can't be parsed as valid JSON, or the decision isn't
    one of the three allowed values, we fail safe by escalating — this way
    a parsing bug never silently closes a ticket incorrectly.
    """
    prompt = build_prompt(short_description, description)

    response = await client.aio.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()

    try:
        data = json.loads(raw_text)
        decision = data["decision"]
        message = data["message"]
        if decision not in ("respond", "ask", "escalate"):
            raise ValueError(f"Unexpected decision value: {decision}")
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        #If Gemini's reply can't be parsed as valid JSON, or the decision isn't  one of the three allowed values, we fail safe by escalating
        logger.error("Could not parse Gemini response (%s). Raw text: %s", exc, raw_text)
        decision = "escalate"
        message = "Automated triage could not determine a fix; escalated for manual review." 

    return decision, message
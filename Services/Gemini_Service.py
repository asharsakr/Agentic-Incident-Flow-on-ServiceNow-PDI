import os
import json
import logging
from google import genai
from dotenv import load_dotenv
from google.genai import types

logger = logging.getLogger("task0")
load_dotenv()

client = genai.Client(api_key=os.environ["gemini_api"]) # 1- uploading the API key for gemini
# 2-loading the five knowledge base articles
_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "AI_Engineering_Task0_Assets", "kb_articles.json")
with open(_KB_PATH, "r") as f:
    kb_articles = json.load(f)["articles"]

def build_prompt(short_description: str, description: str) -> str: # this function is used to commit the prompt to Gemini

    articles_block = "\n".join(f"{a['id']}. {a['text']}" for a in kb_articles)
    return f"""You are an IT support triage assistant. You must decide what
to do with a support ticket using only the knowledge base articles below.
Do not use any outside knowledge, and do not guess at fixes that are not
explicitly listed here.

Knowledge base articles:
{articles_block}

TICKET:
Short description: {short_description}
Description: {description if description else "(no further detail provided)"}

Decide exactly one of the following:
1- "respond": an article clearly covers this AND the ticket gives enough
  concrete detail (a specific symptom, an error, what was already tried,
  when it started) that you're confident the article's fix is the right
  one to apply.
2- "ask": an article's TOPIC matches the ticket, but the description adds
  no real detail beyond restating the same general complaint (e.g. "it
  doesn't work," "it's broken," "not working") you cannot yet tell
  which specific fix applies, so ask a clarifying question first.
3- "escalate": no article's topic covers this problem at all.

Important: matching the general topic of an article is not enough on its
own for "respond." Example ticket "Cannot send email" / "It just
doesn't work" only restates the short description with no new
information, so even though article 2 is topically related, the correct
decision is "ask," not "respond."

Reply with ONLY valid JSON  no markdown formatting, no code fences, no
explanation text before or after in exactly this shape:
{{"decision": "respond" | "ask" | "escalate", "message": "a short, clear message"}}

If you decide "respond", the message should be the fix instructions.
If you decide "ask", the message should be the clarifying question to send
the customer.
If you decide "escalate", the message should briefly explain why."""
async def get_decision(short_description: str, description: str) -> tuple[str, str]: 
    prompt = build_prompt(short_description, description)

    response = await client.aio.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0)
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
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

# 3-loading the triage prompt template 
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompt.txt")
with open(_PROMPT_PATH, "r") as f:
    _PROMPT_TEMPLATE = f.read()

def build_prompt(short_description: str, description: str) -> str: # this function is used to commit the prompt to Gemini

    articles_block = "\n".join(f"{a['id']}. {a['text']}" for a in kb_articles)
    description_text = description if description else "(no further detail provided)"

    return _PROMPT_TEMPLATE.format(
        articles_block=articles_block,
        short_description=short_description,
        description=description_text,
    )

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
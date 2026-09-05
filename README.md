# Agentic Incident Flow
This is a small service that watches for new ServiceNow incidents, asks
Gemini to decide what to do with them using a fixed knowledge base, and
writes the decision back onto the same ticket.

## What you'll need before starting

- A Windows, Mac, or Linux machine
- A free ServiceNow developer instance 
- A free Gemini API key
- ngrok (or any free tunneling tool) 

## Step 1 — Install Python 3.11

**Use Python 3.11, not the newest version available.** If you're on Windows
and already have Python 3.14 installed, that's fine you don't need to
remove it, just install 3.11 alongside it.

```
winget install Python.Python.3.11
```
Why: some of this project's dependencies (specifically `pydantic`) don't
yet have prebuilt installers for very new Python versions. If you try to
install them on 3.14, pip will attempt to compile them from source, which
fails unless you have a C++ compiler and Rust toolchain set up a much
bigger headache than just using a stable Python version.

## Step 2 — Create and activate a virtual environment only when you have two python versions 

From inside this project's folder:
py -3.11 -m venv venv
Then activate it:
- **Windows (PowerShell)**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

If Windows gives you an error like *"running scripts is disabled on this
system"*, run this once (it's safe, and only affects your own user account):
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
Then try activating again.

You'll know it worked when your terminal prompt starts with `(venv)`.
**Do this every single time you open a new terminal for this project** —
activation doesn't persist between terminal sessions.

## Step 3 — Install dependencies

With your `(venv)` active:
pip install -r requirements.txt
This should install cleanly and quickly. 

## Step 4 — Set up your secrets

Open `.env` in a plain text editor and fill in all four values:

gemini_api=your-key-here
servicenow_url=https://devXXXXXX.service-now.com
servicenow_user=admin
servicenow_pass=your-password-here

A few notes that'll save you debugging time:

- **`servicenow_url` should have no trailing slash and nothing else appended**
  — just the plain instance URL. Don't paste a login link or a URL with
  query parameters in it.
- Get your Gemini key at aistudio.google.com → "Get API key" → "Create API
  key". It's free, no credit card needed.
- Never commit the real `.env` file ; it's already listed in `.gitignore`.

## Step 5 — Confirm your ServiceNow credentials actually work for the API
This step matters more than it looks. Some ServiceNow instances block
Basic Auth for API calls even when your username and password are
completely correct usually because of MFA enforcement or a newer
security feature called "Basic Auth Restrictions."

Test it directly, before running any of your own code:
curl.exe -u "admin:yourpassword" "https://your-instance.service-now.com/api/now/table/incident?sysparm_limit=1"

- If you get back real incident JSON ; you're good, move on.
- If you get a 401 error ; log into your ServiceNow instance in the browser,
  search for "Basic Auth Exceptions" or check the admin user's Multi-Factor
  Authentication settings, and resolve that before continuing. No amount of
  fixing the Python code will help if the instance itself is blocking the
  request.

## Step 6 — Run the service

uvicorn main:app --reload --port 8000
Leave this terminal open and running. 

## Step 7 — Expose it to the internet with ngrok

Open a **second terminal** (don't close the first one):
ngrok http 8000

You'll get a public URL that looks like `https://something-random.ngrok-free.dev`.
This changes every time you restart ngrok on the free tier, so if you
restart it later, come back and redo Step 8 with the new URL.

## Step 8 — Connect ServiceNow to your service

1. Follow `pdi_guide.md` to create a Business Rule in your PDI.
2. Paste in `business_rule.js`.
3. Find the line with `YOUR_ENDPOINT` and replace just that part with your
   ngrok URL, keeping `/webhook` at the end:
4. Save it.

## Step 9 — Test it for real

Create a new incident in ServiceNow with a short description like
*"Printer not printing after office move."*

Watch your uvicorn terminal within a few seconds you should see:
1. A `202 Accepted` log line (the webhook received it)
2. A Gemini call
3. A `PATCH ... 200 OK` (the write-back succeeded)

Then go check the incident in ServiceNow ; it should be resolved, with the
fix written into the close notes.
Repeat with the other two test tickets from `test_incidents.json` to confirm
all three decision paths (respond, ask, escalate) work correctly.

## Troubleshooting quick reference

| Symptom | Likely cause |
|---|---|
| `502 Bad Gateway` from ngrok | Your uvicorn server isn't running, or crashed on startup |
| App crashes immediately on startup | Check `.env` variable names match exactly what the code reads, and that `load_dotenv()` runs before the service modules are imported |
| `401 Unauthorized` on the ServiceNow write-back, despite correct credentials | Check Basic Auth Exceptions / MFA settings on the ServiceNow admin account |
| Ticket never gets updated, no errors in the terminal | Double check your ngrok URL in the Business Rule matches your *current* ngrok session |
| `pydantic-core` fails to build during `pip install` | You're not actually inside the Python 3.11 virtual environment |

## Project structure
main.py                          FastAPI app + webhook endpoint
services/gemini_service.py       Builds the prompt, calls Gemini, parses the decision
services/servicenow_service.py   Writes the decision back to ServiceNow
kb_articles.json                 The 5 knowledge base articles used in the prompt
requirements.txt                 Python dependencies
reflection.md                    Reflection on the hardest parts and what I'd improve
Link of the Test Video : https://drive.google.com/file/d/11MZuBOJ5FsS1suMmvUslXOcCE1nJpFwy/view?usp=sharing
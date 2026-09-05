# Project Reflection: Agentic Incident Flow

## The Hardest Part

Surprisingly, the hardest part wasn't the AI logic; it was the environment and authentication plumbing around it.

I started on **Python 3.14**, which turned out to be too new for some of the required libraries. `pydantic` needed to compile a Rust component from source, which failed because I didn't have a C++ linker installed.

The fix was installing **Python 3.11** alongside 3.14 and creating a virtual environment pinned to that version. A good lesson that **"newest is best" isn't always true for dependency compatibility.**

The second, and honestly bigger, challenge was **ServiceNow authentication**.

My webhook was receiving tickets correctly and Gemini was returning decisions, but every write-back to ServiceNow failed with a **401 Unauthorized**, even though I could log into the ServiceNow UI with the exact same username and password.

I had to methodically rule out causes one at a time:

1. PowerShell quoting issues with special characters in the password.
2. A malformed instance URL.
3. A newer ServiceNow security feature (**Basic Auth Restrictions / MFA enforcement**) that blocks API-level Basic Auth even when the credentials are completely valid.

Debugging this required testing the raw HTTP request outside of my own code to prove the problem wasn't in my Python implementation. It turned out to be an **instance-level security setting** I hadn't known existed.

## What Would I Improve With More Time?

### 1. Move Off Basic Auth Entirely

I'd switch to an **OAuth token** for the ServiceNow integration instead of a username/password pair. It's the more secure, production-appropriate approach and avoids the exact authentication issue I encountered.

### 2. Add a Proper Test Suite

Right now, correctness is verified by manually creating tickets and watching the logs.

I'd add automated tests that **mock the Gemini and ServiceNow calls**, so the webhook logic and duplicate-protection logic can be verified without needing a live PDI or API key.

### 3. Persist the Duplicate-Processing Guard

The in-memory `set` works for this task, but it resets every time the service restarts.

A lightweight database, such as **SQLite**, would make the duplicate-processing guard durable across restarts.

### 4. Handle the ngrok URL Rotation Problem

Every time I restart **ngrok** on the free tier, the public URL changes, and I have to manually update the Business Rule.

With more time or a paid ngrok plan, I'd use a **static domain** or add a small script that automatically updates the Business Rule through the ServiceNow API whenever the tunnel restarts.

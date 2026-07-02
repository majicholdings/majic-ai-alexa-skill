"""Alexa-hosted Python entry point for the Majic AI voice skill.

This Lambda is the Alexa-facing bridge to the *private* Majic AI Director. Amazon
verifies the request signature before invoking this function, then this handler
forwards the Alexa Skills Kit (ASK) request envelope to the Majic backend
(``POST /api/alexa/majic``) and returns the ASK response the backend produces.

The Majic Director itself is never exposed here: the backend endpoint is the only
public front door, and it decides the underlying local node/model. No public AI
provider is on this path, and NO secrets are stored in this file — the backend URL
is read from the ``MAJIC_ALEXA_ENDPOINT`` environment variable (set in the Alexa
Developer Console under Code > Environment Variables, or on your own hosting).

If the backend cannot be reached, the handler still returns a well-formed spoken
response so the device never errors out.
"""

import json
import os
import urllib.error
import urllib.request

# Public front door to the private Majic Director. Override in the Alexa console /
# Lambda environment. Never hard-code secrets or private hostnames that require
# credentials here.
DEFAULT_ENDPOINT = "https://api.appmajic.ai/api/alexa/majic"

# Seconds to wait for the backend. Alexa allows a custom skill up to ~8s to
# respond, so keep this comfortably under that ceiling.
REQUEST_TIMEOUT_SEC = 7

LAUNCH_SPEECH = (
    "Majic here. Ask me anything, or ask Majic to help with something. "
    "What would you like to know?"
)
HELP_SPEECH = (
    "You can ask Majic almost anything. For example, say: ask Majic to "
    "summarize today's tasks, or, ask Majic what it can do. "
    "What would you like to ask?"
)
REPROMPT = "What would you like to ask Majic?"
UNREACHABLE_SPEECH = (
    "I'm having trouble reaching Majic right now. Please try again in a moment."
)


def _endpoint():
    url = (os.environ.get("MAJIC_ALEXA_ENDPOINT") or DEFAULT_ENDPOINT).strip()
    return url or DEFAULT_ENDPOINT


def _speak(text, end_session, reprompt=None):
    """Build a minimal ASK response envelope."""
    body = {
        "outputSpeech": {"type": "PlainText", "text": text},
        "card": {"type": "Simple", "title": "Majic", "content": text},
        "shouldEndSession": end_session,
    }
    if reprompt:
        body["reprompt"] = {
            "outputSpeech": {"type": "PlainText", "text": reprompt}
        }
    return {"version": "1.0", "response": body}


def _forward(event):
    """Forward the raw ASK envelope to the Majic backend and return its response.

    Raises on any transport/decode failure so the caller can fall back to a
    local spoken response.
    """
    data = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        _endpoint(),
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
        payload = resp.read().decode("utf-8")
    return json.loads(payload)


def _local_fallback(event):
    """Answer without the backend so the device still gets a sensible reply."""
    request = (event or {}).get("request") or {}
    req_type = request.get("type") or ""

    if req_type == "SessionEndedRequest":
        return {"version": "1.0", "response": {"shouldEndSession": True}}

    if req_type == "LaunchRequest":
        return _speak(LAUNCH_SPEECH, end_session=False, reprompt=REPROMPT)

    if req_type == "IntentRequest":
        name = (request.get("intent") or {}).get("name") or ""
        if name == "AMAZON.HelpIntent":
            return _speak(HELP_SPEECH, end_session=False, reprompt=REPROMPT)
        if name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
            return _speak("Goodbye.", end_session=True)

    return _speak(UNREACHABLE_SPEECH, end_session=True)


def lambda_handler(event, context):
    """Alexa-hosted skill entry point."""
    try:
        return _forward(event)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        # Network error, timeout, non-JSON body, etc. Degrade gracefully.
        return _local_fallback(event)

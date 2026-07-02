# Majic AI — Alexa-hosted (Python) skill

Public-safe **import package** for the **Majic AI** voice skill, laid out for the
Alexa Developer Console *"Import skill"* flow (Alexa-hosted, Python).

Speak a question to an Echo device and hear the answer spoken back. The skill is a
thin, Amazon-verified bridge to the **private Majic AI Director**: the Alexa-hosted
Lambda forwards the request to the Majic backend (`POST /api/alexa/majic`), which
routes the query through the private local stack and speaks the reply back.
**No public AI provider is on this path**, and **no secrets are committed to this
repo** — the backend URL is supplied at runtime via an environment variable.

> This repository contains only the skill package and the Alexa-hosted Lambda
> code. It creates nothing on Amazon by itself. Creating/importing, building, and
> testing the skill all happen in your own Amazon developer account.

## Importing into the Alexa Developer Console

1. Go to <https://developer.amazon.com/alexa/console/ask> → **Create Skill**.
2. Name it **Majic AI**, choose the **Custom** model and **Alexa-hosted (Python)**
   hosting.
3. On the next screen choose **Import skill** and paste this repository's public
   Git URL. The console reads `ask-resources.json` and pulls in `skill-package/`
   (manifest + interaction model) and `lambda/` (Python code).
4. Wait for the initial build to finish.
5. Open **Code → Environment Variables** and set:

   | Variable | Value | Notes |
   | --- | --- | --- |
   | `MAJIC_ALEXA_ENDPOINT` | `https://api.appmajic.ai/api/alexa/majic` | The public front door to your private Majic Director. Change if you host it elsewhere. Defaults to this value if unset. |

6. **Deploy** the code, then open the **Test** tab, switch to **Development**, and
   say/type: *"ask Majic AI what it can do"*.

## What's in this repo

```
.
├── ask-resources.json                         # ASK CLI v2 project descriptor (Alexa-hosted Python)
├── README.md
├── .gitignore
├── skill-package/
│   ├── skill.json                              # Skill manifest (name "Majic AI", PRIVATE distribution)
│   └── interactionModels/custom/en-US.json     # Invocation "majic ai" + AskMajicIntent (AMAZON.SearchQuery)
└── lambda/
    └── py/
        ├── lambda_function.py                  # Alexa-hosted entry point: forwards ASK envelope to the Majic backend
        └── requirements.txt                    # No third-party deps (stdlib only)
```

- **Name / invocation.** Publishing name is **Majic AI**; the invocation name is
  `majic ai`, so users say *"Alexa, ask Majic AI to …"*. A leading carrier word
  (`to`, `what`, `how`, …) is required by the `AMAZON.SearchQuery` slot — prefer
  *"ask Majic AI **to** …"*.
- **Endpoint.** Because this is **Alexa-hosted**, Amazon provisions the Lambda and
  wires it as the skill endpoint automatically. The manifest therefore does **not**
  contain an HTTPS endpoint URI (unlike a self-managed skill). Amazon also verifies
  the ASK request signature before invoking the Lambda.
- **The Lambda** (`lambda/py/lambda_function.py`) forwards the incoming ASK request
  envelope to `MAJIC_ALEXA_ENDPOINT` and returns the backend's ASK response. If the
  backend is unreachable it returns a graceful spoken message so the device never
  errors out. It uses only the Python standard library.

## Configuration you must do after import

Nothing sensitive lives in this repo. To make the skill answer for real:

1. **Set `MAJIC_ALEXA_ENDPOINT`** on the Alexa-hosted Lambda (see step 5 above) to
   your live Majic backend URL. It must be reachable over HTTPS with a publicly
   trusted certificate.
2. **Bind the backend to this skill.** On the Majic backend, set
   `Alexa:MajicSkillId` (env: `Alexa__MajicSkillId`) to this skill's **Skill ID**
   (`amzn1.ask.skill.<guid>`, shown in the console). The backend then fail-closes on
   requests whose application id doesn't match, and enforces request-timestamp
   freshness.
3. Redeploy the backend if you changed its config.

### Credentials — where they live (NOT here)

- **Alexa "Skill Messaging" / Login-with-Amazon client id & client secret** (used
  for proactive/messaging or account-linking flows) are configured in the **Alexa
  Developer Console** (Build → *Permissions* / *Account Linking*) and/or supplied to
  the backend via **environment variables** — they are **never committed to this
  repository**.
- Amazon developer credentials / LWA tokens for the ASK CLI (`ASK_ACCESS_TOKEN`,
  `ASK_REFRESH_TOKEN`, `ASK_VENDOR_ID`) live only on your machine (`ask configure`)
  or in CI secrets — never in this repo.
- The private Majic Director URL/model come from the backend's own configuration,
  not from anything in this package.

## Getting it onto your own Echo (no public certification)

A **development-stage** skill is invocable on Echo devices signed in to the **same
Amazon account / household** as the developer account that owns it — no store
listing, no certification. Keep `distributionMode` as `PRIVATE`, deploy to
Development, and say *"Alexa, ask Majic AI to …"*.

## Caveats for the Alexa import

- **Folder layout.** This package uses `lambda/py/` (matching the ASK CLI Python
  convention) and `ask-resources.json` points `code.default.src` at `./lambda/py`.
  Some newer Alexa-hosted flows expect a **flat** `lambda/` folder. If the import or
  hosted build cannot find the code, move `lambda_function.py` and
  `requirements.txt` up to `lambda/` and change `code.default.src` in
  `ask-resources.json` to `./lambda`.
- **Runtime.** `ask-resources.json` requests `python3.9`. If your Amazon region
  offers only newer runtimes, bump that value (e.g. `python3.12`) — the code is
  standard-library only and portable across 3.x.
- **Invocation wording.** `AMAZON.SearchQuery` cannot match a bare utterance with no
  carrier word (a plain *"tell Majic AI thanks"* may not route). Prefer *"ask Majic
  AI to …"*. The model ships a broad set of carrier prefixes to cover common cases.
- **Private distribution.** The manifest is `PRIVATE` and US-only. Change
  `distributionMode` / `distributionCountries` in `skill-package/skill.json` only if
  you intend to publish, which then requires certification.

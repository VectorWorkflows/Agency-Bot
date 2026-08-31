<div align="center">

<br />

<pre>
   █████╗  ██████╗ ███████╗███╗   ██╗ ██████╗██╗   ██╗
  ██╔══██╗██╔════╝ ██╔════╝████╗  ██║██╔════╝╚██╗ ██╔╝
  ███████║██║  ███╗█████╗  ██╔██╗ ██║██║      ╚████╔╝
  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║██║       ╚██╔╝
  ██║  ██║╚██████╔╝███████╗██║ ╚████║╚██████╗   ██║
  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝   ╚═╝
</pre>

### AGENCY BOT

**The WhatsApp front door of Vector Workflows — the AI that answers before we do.**

<sub>by <a href="https://vectorworkflows.com"><b>VECTOR WORKFLOWS</b></a> — precision-engineered automation</sub>

<br />

[![Python](https://img.shields.io/badge/PYTHON-3.11+-000000?style=for-the-badge&logo=python&logoColor=00D9FF)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FASTAPI-Webhook_Server-000000?style=for-the-badge&logo=fastapi&logoColor=00D9FF)](https://fastapi.tiangolo.com/)
[![WhatsApp](https://img.shields.io/badge/WHATSAPP-Cloud_API-000000?style=for-the-badge&logo=whatsapp&logoColor=00D9FF)](https://developers.facebook.com/docs/whatsapp)
[![Gemini](https://img.shields.io/badge/GEMINI-Intent_Engine-000000?style=for-the-badge&logo=googlegemini&logoColor=00D9FF)](https://ai.google.dev/)
[![MongoDB](https://img.shields.io/badge/MONGODB-State_Machine-000000?style=for-the-badge&logo=mongodb&logoColor=00D9FF)](https://www.mongodb.com/)

<br />

<sub>🗒️ Internal build — this is the agency's own WhatsApp front-of-house, documented here as a build record rather than a client deliverable.</sub>

<br />

</div>

<br />

## ▍ What is this

Every message a stranger sends to Vector Workflows on WhatsApp lands here first. **Agency Bot** is the layer that greets them, figures out what they actually want, and routes them accordingly — before a human ever has to type a word.

It isn't a chatbot that improvises. It's a **deterministic state machine with an AI classifier bolted on as a fallback** — the opposite of the usual "let the LLM wing it" approach. Menus and button clicks are handled with zero AI calls at all. Only genuinely open-ended free text gets escalated to Gemini, and even then, the model is boxed into a strict four-way decision with a confidence floor — it's not allowed to invent services, prices, or answers that don't exist in the config.

<br />

## ▍ The three journeys

<div align="center">

```
                              incoming WhatsApp message
                                        │
                         ┌──────────────┼──────────────┐
                         │  escape word? │  button/list? │  free text
                         ▼              ▼               ▼
                  menu / human     deterministic    Gemini intent
                    (instant)         routing         classifier
                                    (zero AI)        (confidence ≥ 0.70)
                         │              │               │
                         └──────────────┼───────────────┘
                                        ▼
        ┌───────────────────┬───────────────────────┬────────────────────┐
        │  SERVICE_PURCHASE │  BUSINESS_DIAGNOSIS    │ PORTFOLIO_EXPLORE  │
        │  "I know what I   │  "Look at my workflow  │ "Show me what      │
        │   want"           │   and tell me what's   │  you've built"     │
        │                   │   worth automating"    │                    │
        └───────────────────┴───────────────────────┴────────────────────┘
                                        │
                              anything unclear or low-
                              confidence → HUMAN_REQUEST
```

</div>

**Have a service in mind** → walks the static `SERVICES` catalog (Telegram Scheduler, WhatsApp Lead-Gen, Fault Tracking), shows features and a walkthrough link.

**Figure out what I need** → opens a free-text prompt asking the visitor to describe their process end-to-end, saves it verbatim to MongoDB, and queues it for a 24-hour human review — no AI attempts to diagnose or promise anything here on its own.

**Show what you've built** → an *honestly-labelled* portfolio catalog (`PROJECTS`), each entry tagged with real status (`BUILT`, `DEMO`), real availability (`VERIFICATION_PENDING`, `NOT_PUBLIC`), and links straight to the other two Vector Workflows repos' own walkthroughs and notes.

**Speak with someone** → the universal escape hatch, reachable at any point by literally typing "human," "support," or "agent" — flips the conversation into `HUMAN_REQUEST` and mutes the bot until a person takes over.

<br />

## ▍ Design decisions worth recording

<table>
<tr><td width="30%"><b>Fast path first, AI last</b></td><td>Button and list replies never touch the LLM — they're matched directly against known <code>interactive_id</code>s. Gemini is only invoked when a user types something that can't be deterministically routed by state or keyword.</td></tr>
<tr><td><b>Confidence floor, not vibes</b></td><td>Gemini's intent classification is discarded below <code>0.70</code> confidence and silently downgraded to <code>UNCLEAR</code> → human handoff. A wrong guess is worse than an honest "let me get someone."</td></tr>
<tr><td><b>Config-as-source-of-truth</b></td><td>Services and portfolio projects live in plain Python dicts in <code>config.py</code>, not in a prompt. The classifier is explicitly instructed to <i>never invent services, projects, prices, or URLs</i> — it can only choose a lane, never fabricate agency facts.</td></tr>
<tr><td><b>Signed webhooks only</b></td><td>Every inbound payload is verified against Meta's <code>X-Hub-Signature-256</code> HMAC before it's trusted, using a raw-byte comparison that's timing-attack safe.</td></tr>
<tr><td><b>Instant ack, deferred work</b></td><td>The webhook returns <code>200 OK</code> immediately and hands the payload to a FastAPI <code>BackgroundTask</code> — Meta's retry timeout is never at risk, regardless of how long classification or Mongo writes take.</td></tr>
<tr><td><b>Nothing is ever lost</b></td><td>Every inbound message — text or interactive — is appended verbatim to a per-user <code>chat_history</code> array in MongoDB before any routing logic runs.</td></tr>
</table>

<br />

## ▍ Stack

<div align="center">

| Layer | Technology |
|:--|:--|
| **Messaging channel** | `WhatsApp Cloud API` — list messages, quick-reply buttons, signed webhooks |
| **Server** | `FastAPI` + `uvicorn` — HMAC-verified webhook, background dispatch |
| **Intent engine** | `google-generativeai` (Gemini) — strict JSON, closed taxonomy, confidence-gated |
| **State & memory** | `MongoDB` — per-user state machine, context, full chat history |
| **Config** | `pydantic-settings` — typed environment loading |

</div>

<br />

## ▍ Repository map

```
Agency-Bot/
├── app/
│   ├── main.py                 → FastAPI webhook: signature check, ack, background dispatch
│   ├── core/
│   │   ├── config.py             → Settings, intent taxonomy, service & project catalogs
│   │   └── security.py           → HMAC-SHA256 webhook signature verification
│   ├── logic/
│   │   └── state_machine.py      → The router — all four journeys + escape hatches
│   ├── services/
│   │   ├── ai_agent.py            → Gemini intent classifier (closed taxonomy, confidence floor)
│   │   └── whatsapp.py            → Meta Graph API senders (text / buttons / list messages)
│   └── database/
│       ├── connection.py          → MongoDB Atlas client
│       └── crud.py                → User state, context, chat history, human handoff
├── Dockerfile
└── docker-compose.yml
```

<br />

## ▍ Philosophy

The instinct with agency chatbots is to let an LLM freewheel the whole conversation. This one does the opposite: **the AI is a narrow decision-maker bolted onto a deterministic backbone**, used only where deterministic routing genuinely can't reach — and even there, it's fenced in by a closed taxonomy and a confidence threshold. When in doubt, it doesn't guess. It hands off to a human.

<br />

---

<div align="center">

<sub>Want a bot like this deployed for your own business? <a href="https://vectorworkflows.com"><b>Contact Vector Workflows →</b></a></sub>

<br />

<sub>Crafted by <a href="https://vectorworkflows.com"><b>Vector Workflows</b></a></sub>

</div>

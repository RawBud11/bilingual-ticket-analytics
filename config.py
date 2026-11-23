"""Settings in one place: categories, priorities, SLA targets, business hours,
column names and the thresholds for the "what stands out" sentences.

Puentara is a fictional company used for this demo.

Copied (not imported) from the other Puentara projects so this repo stands alone:
- categories, ROUTING defaults and floors: bilingual-ticket-triage/config.py
- SLA targets, business hours, priority floors: bilingual-sla-tracker/src/config.js
"""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SAMPLE_FILE = PROJECT_DIR / "data" / "sample_export.csv"
OUTPUT_DIR = PROJECT_DIR / "output"

LANGUAGES_UI = ["en", "es"]  # languages of the report and the dashboard

# --- Business hours (team time zone) ----------------------------------------
# Mon-Fri 08:00-18:00. Python numbering: 0 = Monday, 6 = Sunday.
# One setting for the whole team: no holiday calendar, no per-team time zones.
BUSINESS_DAYS = [0, 1, 2, 3, 4]
BUSINESS_START_MINUTE = 8 * 60   # 08:00
BUSINESS_END_MINUTE = 18 * 60    # 18:00
BUSINESS_DAY_MINUTES = BUSINESS_END_MINUTE - BUSINESS_START_MINUTE

# --- First-response SLA per priority (from bilingual-sla-tracker) -----------
# clock "24/7": nights and weekends count (a lost card cannot wait for Monday).
# clock "business": only business minutes count.
SLA_TARGETS = {
    "urgent": {"minutes": 60, "clock": "24/7"},
    "high": {"minutes": 4 * 60, "clock": "business"},
    "normal": {"minutes": 8 * 60, "clock": "business"},
    "low": {"minutes": 16 * 60, "clock": "business"},
}

# --- Categories and priorities ----------------------------------------------
CATEGORIES = [
    "account_access",
    "identity_verification",
    "card_lost_stolen",
    "transfer_failed_pending",
    "charge_dispute",
    "fees",
    "tax_forms",
    "app_bug",
    "general_question",
]
# Used when the export's category is empty or not one of the nine above.
UNCATEGORIZED = "uncategorized"

PRIORITIES = ["low", "normal", "high", "urgent"]  # lowest to highest

# Priority used when the export's priority is empty or not recognized.
# Same defaults as ROUTING in bilingual-ticket-triage.
CATEGORY_DEFAULT_PRIORITY = {
    "card_lost_stolen": "urgent",
    "charge_dispute": "high",
    "account_access": "high",
    "identity_verification": "high",
    "transfer_failed_pending": "high",
    "fees": "normal",
    "tax_forms": "normal",
    "app_bug": "normal",
    "general_question": "low",
}
FALLBACK_PRIORITY = "normal"

# Minimum priority per category. A lost card exported as "low" is still
# measured against the urgent 60-minute, 24/7 target.
CATEGORY_PRIORITY_FLOOR = {
    "card_lost_stolen": "urgent",
    "charge_dispute": "high",
    "account_access": "high",
    "identity_verification": "high",
    "transfer_failed_pending": "high",
}

# --- Input columns -----------------------------------------------------------
# Each column is found by any of these header names. Headers are compared in
# lowercase, without accents, with "_" and "-" read as spaces, so "Ticket ID",
# "ticket_id" and "ticket-id" all match. Covers this project's own headers,
# Zendesk and Freshdesk export names, the Title-case headers of
# bilingual-sla-tracker and Spanish headers. Add your helpdesk's names here.
COLUMN_ALIASES = {
    "ticket_id": ["ticket id", "id", "ticket", "ticket number", "numero de ticket",
                  "id del ticket", "ticket no"],
    "created_at": ["created at", "created", "created time", "requested", "creado",
                   "creado el", "fecha de creacion"],
    "channel": ["channel", "via", "source", "canal", "origen"],
    "language": ["language", "idioma", "requester language", "lang"],
    "subject": ["subject", "title", "asunto", "titulo"],
    "body": ["body", "description", "message", "text", "descripcion", "mensaje"],
    # Zendesk's "Ticket type" (question/incident/...) is not a category, so it
    # is not listed. If your categories live in a custom field, add its name.
    "category": ["category", "categoria", "issue category", "reason"],
    "priority": ["priority", "prioridad"],
    "status": ["status", "estado"],
    "first_response_at": ["first response at", "first response", "first reply",
                          "first responded at", "first reply at",
                          "primera respuesta", "primera respuesta el"],
    "solved_at": ["solved at", "solved", "resolved at", "resolved time",
                  "resolved", "closed time", "resuelto el", "fecha de resolucion"],
    "satisfaction": ["satisfaction", "satisfaction score", "customer satisfaction",
                     "csat", "satisfaccion"],
}
REQUIRED_COLUMNS = ["ticket_id", "created_at"]
# Only used to fill a blank language, then dropped. Every other column that is
# not in COLUMN_ALIASES (customer IDs, emails, assignee, tags...) is dropped on load.
TEXT_COLUMNS = ["subject", "body"]

# Values in the export, compared in lowercase without accents.
PRIORITY_VALUES = {
    "low": "low", "baja": "low",
    "normal": "normal", "medium": "normal", "media": "normal",
    "high": "high", "alta": "high",
    "urgent": "urgent", "urgente": "urgent",
}
SOLVED_STATUSES = {"solved", "resolved", "closed", "resuelto", "cerrado"}
LANGUAGE_VALUES = {
    "en": "en", "english": "en", "ingles": "en",
    "es": "es", "spanish": "es", "espanol": "es",
    "mixed": "mixed", "mixto": "mixed",
    "other": "other", "otro": "other",
}
CHANNEL_VALUES = {
    "email": "email", "e-mail": "email", "mail": "email", "correo": "email",
    "chat": "chat", "chat en vivo": "chat",
    "phone": "phone", "telefono": "phone", "voice": "phone",
}
SATISFACTION_VALUES = {"good": "good", "bad": "bad", "bueno": "good", "malo": "bad",
                       "buena": "good", "mala": "bad"}

# --- Backlog age buckets, in business days ----------------------------------
# (key, lower bound inclusive, upper bound exclusive)
AGE_BUCKETS = [
    ("under_1", 0, 1),
    ("1_to_3", 1, 3),
    ("3_to_7", 3, 7),
    ("7_plus", 7, None),
]

# --- "What stands out" thresholds -------------------------------------------
# Simple rules, no AI. Each sentence only describes the data.
SPANISH_SLOWER_RATIO = 1.25       # Spanish median first reply vs English
SPIKE_RATIO = 2.0                 # a category's week vs its typical week
SPIKE_MIN_TICKETS = 20            # at ~100 tickets a week, smaller jumps are usually noise
SHARE_CHANGE_POINTS = 5           # Spanish share change, percentage points
SHARE_WINDOW_WEEKS = 4            # first N weeks vs last N weeks
OLD_BACKLOG_MIN_TICKETS = 5       # open tickets 7+ business days old
LOW_SLA_SHARE = 0.80              # category met the target less often than this
LOW_SLA_MIN_TICKETS = 10

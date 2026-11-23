"""Generate the synthetic helpdesk export used by the demo.

Usage:  python scripts/generate_data.py --seed 42

Writes data/sample_export.csv: about 1,200 tickets created over 12 weeks
(2026-08-03 to 2026-10-25), exported on Monday 2026-10-26 at 08:00.
Puentara is a fictional company and every row is synthetic. Card numbers are
made-up strings that start with 0000, which no real card does. Customer IDs
look like XXXX-0042.

Planted patterns (put here on purpose, so the report has something to find;
they are not findings about any real team):
- the Spanish share of tickets grows from about 28% to about 50%
- the week of 2026-09-14 has a spike of failed or pending transfer tickets
- Spanish tickets get slower first replies (1.6x the time)
- a tail of old app bug tickets that are never solved

Planted mess (so the cleaning step has work to do):
- 10 duplicate ticket IDs, 4 unreadable created dates
- some blank languages, some categories written with Spanish labels
- 6 lost-card tickets exported as "low" priority
- some open tickets with no first response
"""

import argparse
import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
from analytics.sla import add_business_minutes  # noqa: E402
from analytics.strings import STRINGS  # noqa: E402
from ticket_templates import GROUPS, MERCHANTS, SCREENS  # noqa: E402

OUT_FILE = PROJECT_DIR / "data" / "sample_export.csv"
COLUMNS = ["ticket_id", "created_at", "customer_id", "channel", "language", "subject",
           "category", "priority", "status", "assignee", "first_response_at",
           "solved_at", "satisfaction"]

START = datetime(2026, 8, 3)               # a Monday
WEEKS = 12
EXPORT_TIME = datetime(2026, 10, 26, 8, 0)  # Monday after the last week
TICKETS_PER_WEEK = 95
SPIKE_WEEK, SPIKE_EXTRA = 6, 35             # week of 2026-09-14
SPANISH_SLOWER = 1.6
AGENTS = ["Sam Demo", "Jordan Demo", "Mateo Demo"]  # same demo agents as bilingual-sla-tracker
MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

CATEGORY_WEIGHTS = {
    "account_access": 14, "identity_verification": 8, "card_lost_stolen": 7,
    "transfer_failed_pending": 13, "charge_dispute": 10, "fees": 10,
    "tax_forms": 7, "app_bug": 13, "general_question": 18,
}
DAY_WEIGHTS = [1.2, 1.2, 1.1, 1.1, 1.0, 0.5, 0.4]  # Monday first
HOUR_WEIGHTS = [0.2] * 7 + [1, 2, 2, 2, 2, 2, 2, 2, 2, 1.5] + [1, 1, 0.8, 0.6, 0.5, 0.3, 0.3]

# Hand-written, for the "mixed" and "other" language rows.
MIXED = [("Hi, tengo un problema with my card", "general_question"),
         ("My transfer is pending. Otra cosa, ¿dónde está mi formulario?", "transfer_failed_pending")]
OTHER = [("Bonjour, je n'arrive pas à recevoir mon code. Merci.", "account_access"),
         ("Ciao, non riesco ad aprire l'app.", "app_bug")]


def fill_slots(text, lang, rng):
    """Copied from bilingual-ticket-triage/scripts/make_tickets.py."""
    day = datetime(2026, 9, 1) + timedelta(days=rng.randint(0, 45))
    card = "0000" + "".join(str(rng.randint(0, 9)) for _ in range(12))
    if rng.random() < 0.5:
        sep = rng.choice([" ", "-"])
        card = sep.join(card[i:i + 4] for i in range(0, 16, 4))
    values = {
        "amount": f"${rng.randint(5, 900)}.{rng.randint(0, 99):02d}",
        "fee": f"${rng.choice(['1.99', '2.50', '4.99', '9.00'])}",
        "date": f"{day.day} de {MONTHS_ES[day.month - 1]}" if lang == "es" else day.strftime("%b %d"),
        "merchant": rng.choice(MERCHANTS),
        "screen": rng.choice(SCREENS[lang]),
        "card": card,
        "cvv": str(rng.randint(100, 999)),
        "otp": str(rng.randint(100000, 999999)),
        "last4": f"{rng.randint(0, 9999):04d}",
    }
    return text.format(**values)


def created_time(week, rng, days=range(7)):
    day = rng.choices(list(days), weights=[DAY_WEIGHTS[d] for d in days])[0]
    hour = rng.choices(range(24), weights=HOUR_WEIGHTS)[0]
    return START + timedelta(weeks=week, days=day, hours=hour, minutes=rng.randint(0, 59))


def pick_language(week, rng):
    spanish = 0.28 + 0.22 * week / (WEEKS - 1)  # planted: grows over the period
    roll = rng.random()
    if roll < 0.03:
        return "mixed"
    if roll < 0.04:
        return "other"
    return "es" if roll < 0.04 + spanish else "en"


def first_reply(created, priority, lang, rng):
    """Most replies land inside the SLA; some do not. Spanish waits longer (planted)."""
    slower = SPANISH_SLOWER if lang == "es" else 1.0
    goal = config.SLA_TARGETS[priority]
    share = rng.uniform(0.1, 0.85) if rng.random() > 0.12 else rng.uniform(1.0, 2.5)
    minutes = goal["minutes"] * share * slower
    if goal["clock"] == "24/7":
        return created + timedelta(minutes=minutes)
    return add_business_minutes(created, minutes)


def make_ticket(week, rng, category=None, days=range(7)):
    lang = pick_language(week, rng)
    category = category or rng.choices(list(CATEGORY_WEIGHTS), weights=CATEGORY_WEIGHTS.values())[0]
    group = rng.choice([g for g in GROUPS if g["category"] == category])
    if lang == "mixed":
        subject, category = rng.choice(MIXED)
    elif lang == "other":
        subject, category = rng.choice(OTHER)
    else:
        subject = fill_slots(rng.choice(group[lang]), lang, rng)
    priority = group["urgency"] if group["category"] == category else config.CATEGORY_DEFAULT_PRIORITY[category]
    created = created_time(week, rng, days)
    reply = first_reply(created, priority, lang, rng)
    hours = rng.expovariate(1 / (40 if category == "app_bug" else 18))
    return {"created": created, "lang": lang, "subject": subject, "category": category,
            "priority": priority, "reply": reply, "solved": reply + timedelta(hours=hours),
            "channel": rng.choices(["email", "chat", "phone"], weights=[45, 40, 15])[0]}


def to_row(t, rng):
    reply = t["reply"] if t["reply"] <= EXPORT_TIME and not t.get("no_reply") else None
    solved = t["solved"] if reply and t["solved"] <= EXPORT_TIME and not t.get("never_solved") else None
    status = "solved" if solved else ("open" if reply else "new")
    if status == "open" and rng.random() < 0.4:
        status = "pending"
    label_lang = "es" if rng.random() < 0.12 else "en"  # planted: some Spanish labels
    satisfaction = ""
    if solved and rng.random() < 0.55:
        satisfaction = "good" if rng.random() < 0.85 else "bad"
    return {
        "created_at": t["created"].strftime("%Y-%m-%d %H:%M"),
        "customer_id": f"XXXX-{rng.randint(1, 9999):04d}",
        "channel": t["channel"],
        "language": "" if t["lang"] in ("en", "es") and rng.random() < 0.07 else t["lang"],
        "subject": t["subject"],
        "category": STRINGS[label_lang][f"category.{t['category']}"],
        "priority": t["priority"],
        "status": status,
        "assignee": rng.choice(AGENTS),
        "first_response_at": reply.strftime("%Y-%m-%d %H:%M") if reply else "",
        "solved_at": solved.strftime("%Y-%m-%d %H:%M") if solved else "",
        "satisfaction": satisfaction,
    }


def build(seed):
    rng = random.Random(seed)
    tickets = []
    for week in range(WEEKS):
        tickets += [make_ticket(week, rng) for _ in range(TICKETS_PER_WEEK + rng.randint(-8, 8))]
    # Planted: a transfer spike early in one week.
    tickets += [make_ticket(SPIKE_WEEK, rng, "transfer_failed_pending", days=range(3))
                for _ in range(SPIKE_EXTRA)]
    # Planted: old app bugs nobody closed.
    old_bugs = [t for t in tickets if t["category"] == "app_bug" and t["created"] < START + timedelta(weeks=8)]
    for t in rng.sample(old_bugs, 18):
        t["never_solved"] = True
    # Planted: recent tickets still waiting for a first reply.
    recent = [t for t in tickets if t["created"] >= START + timedelta(weeks=WEEKS - 1)]
    for t in rng.sample(recent, 6):
        t["no_reply"] = True
    # Planted: lost-card tickets exported with a low priority.
    for t in rng.sample([t for t in tickets if t["category"] == "card_lost_stolen"], 6):
        t["priority"] = "low"

    tickets.sort(key=lambda t: t["created"])
    rows = []
    for n, t in enumerate(tickets, start=1):
        row = to_row(t, rng)
        row["ticket_id"] = f"PT-{10000 + n}"
        rows.append(row)

    # Planted mess: duplicates and unreadable dates.
    for row in rng.sample(rows, 10):
        rows.insert(rng.randint(0, len(rows)), dict(row))
    for row, bad in zip(rng.sample(rows, 4), ["31/09/2026 10:15", "2026-09-31 09:00", "yesterday", ""]):
        row["created_at"] = bad
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Generate the synthetic Puentara export (fictional company).")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rows = build(args.seed)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig so Excel shows accents and ñ correctly.
    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_FILE.relative_to(PROJECT_DIR).as_posix()}")


if __name__ == "__main__":
    main()

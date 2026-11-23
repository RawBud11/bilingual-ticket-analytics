"""Every number in the report, as plain pandas tables with keys (not labels).

The report (report.py) and the dashboard (app.py) both call build_report(),
so they always show the same numbers. Labels and languages are added later
in present.py.

Times are in minutes here. "First reply" and "resolution" are wall-clock
minutes from created (what the customer waited). SLA met uses each priority's
own clock (see sla.py).
"""

import pandas as pd

import config

from .sla import business_minutes_between, first_response_outcome

LANGUAGES = ["en", "es", "mixed", "other"]


def latest_time(df):
    """Default "as of": the latest date anywhere in the export."""
    return max(df[c].max() for c in ("created_at", "first_response_at", "solved_at")
               if df[c].notna().any())


def enrich(df, as_of):
    """Add the per-ticket columns every table needs, as seen at `as_of`.
    Tickets created after `as_of` are left out: they did not exist yet."""
    df = df[df["created_at"] <= as_of].copy()
    answered = df["first_response_at"].notna() & (df["first_response_at"] <= as_of)
    solved_by_then = df["solved_at"].notna() & (df["solved_at"] <= as_of)
    df["frt_min"] = ((df["first_response_at"] - df["created_at"]).dt.total_seconds() / 60).where(answered)
    df["resolution_min"] = ((df["solved_at"] - df["created_at"]).dt.total_seconds() / 60).where(solved_by_then)
    df["sla"] = [
        first_response_outcome(p, c, f if pd.notna(f) else None, as_of)
        for p, c, f in zip(df["priority"], df["created_at"], df["first_response_at"])
    ]
    # Solved with no solved date (status only) counts as solved; solved after
    # `as_of` was still open at `as_of`.
    df["open"] = ~(solved_by_then | (df["solved"] & df["solved_at"].isna()))
    df["age_days"] = [
        business_minutes_between(c, as_of) / config.BUSINESS_DAY_MINUTES if is_open else None
        for c, is_open in zip(df["created_at"], df["open"])
    ]
    df["age_bucket"] = df["age_days"].map(age_bucket)
    df["week"] = week_start(df["created_at"])
    return df


def week_start(times):
    """Monday 00:00 of each time's week."""
    return times.dt.to_period("W-SUN").dt.start_time


def age_bucket(days):
    if days is None or pd.isna(days):
        return None
    for key, low, high in config.AGE_BUCKETS:
        if days >= low and (high is None or days < high):
            return key
    return None


def _median(series):
    series = series.dropna()
    return float(series.median()) if len(series) else None


def _share(part, whole):
    return part / whole if whole else None


def weekly_volume(df, as_of):
    weeks = pd.date_range(df["week"].min(), week_start(pd.Series([as_of]))[0], freq="7D")
    created = df.groupby("week").size()
    solved_at = df["solved_at"].where(df["solved_at"] <= as_of).dropna()
    solved = week_start(solved_at).value_counts()
    return pd.DataFrame({
        "week": weeks,
        "created": [int(created.get(w, 0)) for w in weeks],
        "solved": [int(solved.get(w, 0)) for w in weeks],
    })


def top_categories(df):
    """Tickets per category, and the latest week in the data vs the week before."""
    last = df["week"].max()
    prev = last - pd.Timedelta(days=7)
    rows = []
    for category, group in df.groupby("category"):
        last_n = int((group["week"] == last).sum())
        prev_n = int((group["week"] == prev).sum())
        rows.append({"category": category, "tickets": len(group),
                     "last_week": last_n, "prev_week": prev_n, "change": last_n - prev_n})
    table = pd.DataFrame(rows).sort_values(["tickets", "category"], ascending=[False, True])
    return table.reset_index(drop=True)


def speed_by(df, column, order):
    """First reply, SLA met and resolution per group, in a fixed row order."""
    rows = []
    for key in order:
        group = df[df[column] == key]
        if group.empty:
            continue
        known = group["sla"].notna().sum()
        met = (group["sla"] == "met").sum()
        rows.append({
            column: key,
            "tickets": len(group),
            "answered": int(group["frt_min"].notna().sum()),
            "median_frt_min": _median(group["frt_min"]),
            "sla_known": int(known),
            "sla_met": int(met),
            "sla_met_share": _share(met, known),
            "median_resolution_min": _median(group["resolution_min"]),
        })
    return pd.DataFrame(rows)


def backlog_by_age(df):
    open_ = df[df["open"]]
    return pd.DataFrame({
        "age": [key for key, _, _ in config.AGE_BUCKETS],
        "open": [int((open_["age_bucket"] == key).sum()) for key, _, _ in config.AGE_BUCKETS],
    })


def backlog_by_category(df):
    open_ = df[df["open"]]
    rows = []
    for category in config.CATEGORIES + [config.UNCATEGORIZED]:
        group = open_[open_["category"] == category]
        if group.empty:
            continue
        row = {"category": category, "open": len(group)}
        for key, _, _ in config.AGE_BUCKETS:
            row[key] = int((group["age_bucket"] == key).sum())
        rows.append(row)
    return pd.DataFrame(rows, columns=["category", "open"] + [k for k, _, _ in config.AGE_BUCKETS])


def urgent_open(df):
    """Open urgent tickets: ticket ID, category and age only, oldest first."""
    table = df[df["open"] & (df["priority"] == "urgent")]
    table = table.sort_values("age_days", ascending=False)
    return table[["ticket_id", "category", "age_days"]].reset_index(drop=True)


def spanish_by_week(weekly, df):
    spanish = df[df["language"] == "es"].groupby("week").size()
    table = weekly[["week", "created"]].rename(columns={"created": "tickets"}).copy()
    table["spanish_share"] = [_share(int(spanish.get(w, 0)), n)
                              for w, n in zip(table["week"], table["tickets"])]
    return table


def satisfaction(df):
    rows = []
    for language in LANGUAGES:
        group = df[(df["language"] == language) & (df["satisfaction"] != "")]
        if group.empty:
            continue
        good = int((group["satisfaction"] == "good").sum())
        bad = int((group["satisfaction"] == "bad").sum())
        rows.append({"language": language, "good": good, "bad": bad,
                     "good_share": _share(good, good + bad)})
    return pd.DataFrame(rows)


def build_report(df, quality, as_of=None):
    """All tables, key numbers and the enriched ticket table for insights."""
    as_of = as_of or latest_time(df)
    tickets = enrich(df, as_of)
    weekly = weekly_volume(tickets, as_of)
    by_language = speed_by(tickets, "language", LANGUAGES)
    by_language.insert(2, "share", by_language["tickets"] / len(tickets))
    known = tickets["sla"].notna().sum()

    tables = {
        "weekly_volume": weekly,
        "top_categories": top_categories(tickets),
        "frt_by_category": speed_by(tickets, "category", config.CATEGORIES + [config.UNCATEGORIZED]),
        "frt_by_priority": speed_by(tickets, "priority", list(reversed(config.PRIORITIES))),
        "frt_by_language": by_language,
        "spanish_by_week": spanish_by_week(weekly, tickets),
        "backlog_by_age": backlog_by_age(tickets),
        "backlog_by_category": backlog_by_category(tickets),
        "urgent_open": urgent_open(tickets),
    }
    if quality.get("has_satisfaction"):
        tables["satisfaction"] = satisfaction(tickets)

    kpis = {
        "tickets": len(tickets),
        "median_frt": _median(tickets["frt_min"]),
        "sla_met": _share((tickets["sla"] == "met").sum(), known),
        "open_backlog": int(tickets["open"].sum()),
        "spanish_share": _share((tickets["language"] == "es").sum(), len(tickets)),
    }
    return {
        "as_of": as_of,
        "period": (tickets["created_at"].min(), tickets["created_at"].max()),
        "quality": quality,
        "kpis": kpis,
        "tables": tables,
        "tickets": tickets,
    }

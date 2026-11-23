"""The "what stands out" sentences: simple threshold rules, no AI.

Each rule returns (sentence key in strings.py, values) or nothing. Sentences
only describe the data. They never recommend, predict or promise anything
(a test checks the templates for words like "reduce" or "guarantee").
Thresholds live in config.py.
"""

import pandas as pd

import config


def spanish_slower(report):
    table = report["tables"]["frt_by_language"].set_index("language")
    if not {"en", "es"} <= set(table.index):
        return None
    en, es = table.loc["en", "median_frt_min"], table.loc["es", "median_frt_min"]
    if not en or not es or pd.isna(en) or pd.isna(es):
        return None
    if es > config.SPANISH_SLOWER_RATIO * en:
        return ("insight.spanish_slower", {"ratio": round(es / en, 1), "es": es, "en": en})
    return None


def spikes(report):
    """A category whose busiest week is far above its typical (median) week."""
    tickets = report["tickets"]
    weeks = report["tables"]["weekly_volume"]["week"]
    found = []
    for category, group in tickets.groupby("category"):
        counts = group.groupby("week").size().reindex(weeks, fill_value=0)
        typical = float(counts.median())
        week, count = counts.idxmax(), int(counts.max())
        if count >= config.SPIKE_MIN_TICKETS and count >= config.SPIKE_RATIO * max(typical, 1):
            found.append(("insight.spike", {"category": category, "week": week,
                                            "count": count, "typical": round(typical)}))
    return sorted(found, key=lambda item: -item[1]["count"])


def spanish_share_change(report):
    """First N weeks vs last N weeks, counting tickets (not averaging weeks)."""
    table = report["tables"]["spanish_by_week"]
    n = config.SHARE_WINDOW_WEEKS
    if len(table) < 2 * n:
        return None

    def share(rows):
        total = rows["tickets"].sum()
        return (rows["tickets"] * rows["spanish_share"].fillna(0)).sum() / total if total else None

    start, end = share(table.head(n)), share(table.tail(n))
    if start is None or end is None:
        return None
    if abs(end - start) * 100 >= config.SHARE_CHANGE_POINTS:
        return ("insight.spanish_share_change", {"start": start, "end": end, "weeks": n})
    return None


def old_backlog(report):
    tickets = report["tickets"]
    old = tickets[tickets["open"] & (tickets["age_bucket"] == "7_plus")]
    if len(old) < config.OLD_BACKLOG_MIN_TICKETS:
        return None
    counts = old["category"].value_counts()
    top = sorted(counts.index, key=lambda c: (-counts[c], c))[0]
    return ("insight.old_backlog", {"count": len(old), "top_count": int(counts[top]),
                                    "category": top})


def low_sla(report):
    table = report["tables"]["frt_by_category"]
    table = table[table["sla_known"] >= config.LOW_SLA_MIN_TICKETS].dropna(subset=["sla_met_share"])
    if table.empty:
        return None
    worst = table.sort_values(["sla_met_share", "category"]).iloc[0]
    if worst["sla_met_share"] >= config.LOW_SLA_SHARE:
        return None
    return ("insight.low_sla", {"category": worst["category"], "share": worst["sla_met_share"],
                                "met": int(worst["sla_met"]), "total": int(worst["sla_known"])})


def find_insights(report):
    found = [spanish_slower(report), *spikes(report), spanish_share_change(report),
             old_backlog(report), low_sla(report)]
    return [item for item in found if item]

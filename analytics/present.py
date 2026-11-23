"""Turn the numbers from metrics.py into labeled tables and sentences in EN or ES.

Shared by report.py and app.py, so the report and the dashboard use the same
headers and labels. Shares become percentages (0-100) and minutes become
hours, both with one decimal, so the CSV tables stay numeric.
"""

import pandas as pd

from .strings import STRINGS, hours, pct, t

FRT_COLUMNS = [("tickets", "int"), ("answered", "int"), ("median_frt_min", "hours"),
               ("sla_known", "int"), ("sla_met", "int"), ("sla_met_share", "pct"),
               ("median_resolution_min", "hours")]

# Table name -> [(column, kind)]. The kind says how to show the value.
TABLE_COLUMNS = {
    "weekly_volume": [("week", "week"), ("created", "int"), ("solved", "int")],
    "top_categories": [("category", "category"), ("tickets", "int"), ("last_week", "int"),
                       ("prev_week", "int"), ("change", "int")],
    "frt_by_category": [("category", "category"), *FRT_COLUMNS],
    "frt_by_priority": [("priority", "priority"), *FRT_COLUMNS],
    "frt_by_language": [("language", "language"), ("tickets", "int"), ("share", "pct"),
                        *FRT_COLUMNS[1:]],
    "spanish_by_week": [("week", "week"), ("tickets", "int"), ("spanish_share", "pct")],
    "backlog_by_age": [("age", "age"), ("open", "int")],
    "backlog_by_category": [("category", "category"), ("open", "int"), ("under_1", "int"),
                            ("1_to_3", "int"), ("3_to_7", "int"), ("7_plus", "int")],
    "urgent_open": [("ticket_id", "text"), ("category", "category"), ("age_days", "days")],
    "satisfaction": [("language", "language"), ("good", "int"), ("bad", "int"),
                     ("good_share", "pct")],
}
TABLE_ORDER = list(TABLE_COLUMNS)

HEADER_KEYS = {"median_frt_min": "col.median_frt_h",
               "median_resolution_min": "col.median_resolution_h",
               "under_1": "age.under_1", "1_to_3": "age.1_to_3",
               "3_to_7": "age.3_to_7", "7_plus": "age.7_plus"}


def label(lang, kind, value):
    """Category/priority/language/channel/age key -> label. load.py only lets
    known keys through, so the fallback (show the value) is a safety net."""
    key = f"{kind}.{value}"
    return t(lang, key) if key in STRINGS[lang] else str(value)


def _value(lang, kind, value):
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    if kind == "int":
        return int(value)
    if kind == "hours":
        return round(value / 60, 1)
    if kind == "pct":
        return round(value * 100, 1)
    if kind == "days":
        return round(value, 1)
    if kind == "week":
        return value.strftime("%Y-%m-%d")
    if kind == "text":
        return str(value)
    return label(lang, kind, value)


def localize_table(lang, name, table):
    """A metrics table with headers and labels in `lang`."""
    columns = TABLE_COLUMNS[name]
    out = pd.DataFrame({
        t(lang, HEADER_KEYS.get(col, f"col.{col}")): [_value(lang, kind, v) for v in table[col]]
        if col in table.columns else []
        for col, kind in columns
    })
    return out


def time_text(value):
    return value.strftime("%Y-%m-%d %H:%M")


def kpi_lines(lang, kpis):
    """[(label, value as text)] for the five key numbers."""
    return [
        (t(lang, "kpi.tickets"), str(kpis["tickets"])),
        (t(lang, "kpi.median_frt"), t(lang, "unit.hours", value=hours(kpis["median_frt"]))),
        (t(lang, "kpi.sla_met"), pct(lang, kpis["sla_met"])),
        (t(lang, "kpi.open_backlog"), str(kpis["open_backlog"])),
        (t(lang, "kpi.spanish_share"), pct(lang, kpis["spanish_share"])),
    ]


QUALITY_KEYS = ["rows_read", "duplicates", "bad_dates", "other_dates", "language_filled",
                "priority_raised", "uncategorized", "dropped_columns", "rows_used"]


def quality_lines(lang, quality):
    return [t(lang, f"dq.{key}", n=quality[key]) for key in QUALITY_KEYS]


def insight_lines(lang, insights):
    if not insights:
        return [t(lang, "insight.none")]
    lines = []
    for key, values in insights:
        template = STRINGS[lang][key]
        shown = {}
        for name, value in values.items():
            if name == "category":
                text = label(lang, "category", value)
                # Lowercase the label inside a sentence ("... of them are app bug").
                shown[name] = text if template.startswith("{category}") else text[0].lower() + text[1:]
            elif name in ("start", "end", "share"):
                shown[name] = pct(lang, value)
            elif name in ("es", "en"):
                shown[name] = hours(value)
            elif name == "week":
                shown[name] = value.strftime("%Y-%m-%d")
            else:
                shown[name] = value
        lines.append(t(lang, key, **shown))
    return lines

"""Load a helpdesk CSV export (Zendesk, Freshdesk or a spreadsheet) and clean it.

What cleaning does, in order:
1. Find each column by its English or Spanish header or a known alias.
   Every other column is dropped right away: customer IDs, emails, assignee,
   tags. Subject and body are kept only to fill a blank language, then dropped.
2. Remove duplicate ticket IDs (keep the first row).
3. Read dates. Rows with an unreadable created date are skipped; unreadable
   first reply / solved dates (or ones before created) are ignored.
4. Map category labels in English or Spanish to the nine shared keys.
5. Fill a blank language with the detector (en / es / mixed / other).
6. Apply the category priority floor (a lost card is always urgent).

Returns the clean table and a data-quality dict with a count for each step.
"""

import io
import unicodedata

import pandas as pd

import config

from .language import detect_language
from .sla import parse_time
from .strings import STRINGS

PRIORITY_RANK = {p: i for i, p in enumerate(config.PRIORITIES)}


class LoadError(Exception):
    """A problem the user can fix. `key` is a message in strings.py."""

    def __init__(self, key, **values):
        super().__init__(key)
        self.key = key
        self.values = values


def fold(text):
    """Lowercase, no accents, "_" and "-" read as spaces: "Categoría" -> "categoria"."""
    text = unicodedata.normalize("NFD", str(text).lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(text.replace("_", " ").replace("-", " ").split())


def find_columns(headers):
    """{our column name: header in the file}, for the columns we recognize."""
    folded = {}
    for header in headers:
        folded.setdefault(fold(header), header)  # first header wins
    found = {}
    for column, aliases in config.COLUMN_ALIASES.items():
        for alias in [column, *aliases]:
            if fold(alias) in folded:
                found[column] = folded[fold(alias)]
                break
    return found


def category_lookup():
    """Category key or label (English or Spanish), folded -> category key."""
    lookup = {}
    for key in config.CATEGORIES:
        lookup[fold(key)] = key
        for lang in STRINGS:
            lookup[fold(STRINGS[lang][f"category.{key}"])] = key
    return lookup


def read_csv(source):
    """Read every cell as text. `source` is a path, bytes or a file object."""
    data = source if isinstance(source, bytes) else None
    if data is None and hasattr(source, "read"):
        data = source.read()
    # utf-8-sig handles files with or without a BOM. Excel on Windows often
    # saves "CSV" as cp1252, so that is the second try.
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            target = io.BytesIO(data) if data is not None else source
            return pd.read_csv(target, dtype=str, keep_default_na=False, encoding=encoding)
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            raise LoadError("error.file_not_found", path=str(source)) from None
        except (pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            raise LoadError("error.unreadable", detail=str(error).strip()) from None
    raise LoadError("error.unreadable", detail="unknown text encoding")


def _dates(series, created=None):
    """Parse a column of date text. Returns (datetimes, how many were unreadable).
    A date before `created` is a typing mistake, so it counts as unreadable."""
    parsed = pd.to_datetime(series.map(parse_time))
    bad = (series != "") & parsed.isna()
    if created is not None:
        bad |= parsed < created
    return parsed.mask(bad), int(bad.sum())


def _priority(category, exported):
    """(priority used for the SLA, True if the floor raised it)."""
    default = config.CATEGORY_DEFAULT_PRIORITY.get(category, config.FALLBACK_PRIORITY)
    priority = exported or default
    floor = config.CATEGORY_PRIORITY_FLOOR.get(category)
    if floor and PRIORITY_RANK[floor] > PRIORITY_RANK[priority]:
        return floor, bool(exported)  # a blank priority is filled, not "raised"
    return priority, False


def load_export(source):
    raw = read_csv(source)
    columns = find_columns(raw.columns)
    missing = [c for c in config.REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise LoadError("error.missing_columns", columns=", ".join(missing))

    quality = {"rows_read": len(raw), "dropped_columns": len(raw.columns) - len(columns)}
    df = raw[list(columns.values())].copy()
    df.columns = list(columns.keys())
    for column in config.COLUMN_ALIASES:  # optional columns become blank
        if column not in df.columns:
            df[column] = ""
    df = df.apply(lambda s: s.str.strip())

    before = len(df)
    df = df.drop_duplicates("ticket_id", keep="first")
    quality["duplicates"] = before - len(df)

    df["created_at"], _ = _dates(df["created_at"])
    quality["bad_dates"] = int(df["created_at"].isna().sum())  # blank or unreadable
    df = df[df["created_at"].notna()].copy()
    if df.empty:
        raise LoadError("error.empty")
    df["first_response_at"], bad_fr = _dates(df["first_response_at"], df["created_at"])
    df["solved_at"], bad_solved = _dates(df["solved_at"], df["created_at"])
    quality["other_dates"] = bad_fr + bad_solved

    lookup = category_lookup()
    df["category"] = df["category"].map(lambda v: lookup.get(fold(v), config.UNCATEGORIZED))
    quality["uncategorized"] = int((df["category"] == config.UNCATEGORIZED).sum())

    # A value we do not recognize ("fr", "pt") is a real language, just not one
    # we report on separately, so it becomes "other". Blank gets detected.
    df["language"] = df["language"].map(
        lambda v: config.LANGUAGE_VALUES.get(fold(v), "other") if v else "")
    blank = df["language"] == ""
    text = df["subject"] + " " + df["body"]
    df.loc[blank, "language"] = text[blank].map(detect_language)
    quality["language_filled"] = int(blank.sum())

    exported = df["priority"].map(lambda v: config.PRIORITY_VALUES.get(fold(v), ""))
    results = [_priority(c, e) for c, e in zip(df["category"], exported)]
    df["priority"] = [p for p, _ in results]
    df["priority_raised"] = [r for _, r in results]
    quality["priority_raised"] = int(df["priority_raised"].sum())

    df["solved"] = df["solved_at"].notna() | df["status"].map(fold).isin(config.SOLVED_STATUSES)
    # Unknown channel values become "other": a free-text cell could hold anything,
    # even a card number, so it is never shown as written.
    df["channel"] = df["channel"].map(lambda v: config.CHANNEL_VALUES.get(fold(v), "other"))
    df["satisfaction"] = df["satisfaction"].map(
        lambda v: config.SATISFACTION_VALUES.get(fold(v), ""))
    quality["has_satisfaction"] = bool((df["satisfaction"] != "").any())
    quality["rows_used"] = len(df)

    # Ticket text never leaves this function.
    keep = ["ticket_id", "created_at", "first_response_at", "solved_at", "channel",
            "language", "category", "priority", "priority_raised", "solved", "satisfaction"]
    return df[keep].reset_index(drop=True), quality

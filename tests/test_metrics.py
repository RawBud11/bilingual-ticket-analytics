"""Numbers for data/tiny_export.csv, worked out by hand.

As of Friday 2026-10-23 17:00. After cleaning: 11 tickets, T1-T11.
First reply, wall-clock minutes (answered tickets):
  T1 30, T2 300, T3 960, T4 3960, T5 60, T6 60, T7 60, T8 90
  sorted 30 60 60 60 90 300 960 3960 -> median (60 + 90) / 2 = 75 min
SLA (business clock unless urgent):
  T1 urgent (raised from low) 30 <= 60 met        T2 high 300 > 240 missed
  T3 normal Tue 17:00 -> Wed 09:00 = 120 met      T4 high Fri 17:30 -> Mon 11:30 = 240 met
  T5 low Saturday, 0 business min met              T6 normal 60 met
  T7 high 60 met                                   T8 urgent 90 > 60 missed
  T9 high, no reply, 1380 business min by as of -> missed
  T10 urgent, no reply, 120 min -> missed
  T11 low, no reply, 30 business min -> not due yet, not counted
  -> 6 met of 10 = 60%
Backlog: T6 (Mon 08:00, 2940 business min = 4.9 days -> 3-7), T9 (2.3 -> 1-3),
  T10 (0.2 -> under 1), T11 (0.05 -> under 1)
Resolution, wall-clock minutes: 180, 1440, 1080, 4110, 90, 1440, 180 -> median 1080
"""

import pytest
from helpers import TINY, TINY_AS_OF

from analytics.load import load_export
from analytics.metrics import age_bucket, build_report, latest_time


@pytest.fixture(scope="module")
def report():
    df, quality = load_export(str(TINY))
    return build_report(df, quality, TINY_AS_OF)


def row(table, column, key):
    return table.set_index(column).loc[key]


def test_key_numbers(report):
    k = report["kpis"]
    assert k["tickets"] == 11
    assert k["median_frt"] == 75
    assert k["sla_met"] == pytest.approx(0.6)
    assert k["open_backlog"] == 4
    assert k["spanish_share"] == pytest.approx(6 / 11)


def test_weekly_created_and_solved(report):
    weekly = report["tables"]["weekly_volume"]
    assert [w.strftime("%Y-%m-%d") for w in weekly["week"]] == ["2026-10-12", "2026-10-19"]
    assert list(weekly["created"]) == [5, 6]
    assert list(weekly["solved"]) == [4, 3]   # T1 T2 T3 T5 | T4 T7 T8


def test_top_categories_week_over_week(report):
    top = report["tables"]["top_categories"]
    assert top.iloc[0]["category"] == "card_lost_stolen"
    lost = row(top, "category", "card_lost_stolen")
    assert (lost["tickets"], lost["last_week"], lost["prev_week"], lost["change"]) == (3, 2, 1, 1)
    fees = row(top, "category", "fees")
    assert (fees["last_week"], fees["prev_week"], fees["change"]) == (0, 1, -1)


def test_speed_by_language(report):
    table = report["tables"]["frt_by_language"]
    en, es = row(table, "language", "en"), row(table, "language", "es")
    assert (en["tickets"], en["median_frt_min"], en["sla_met"], en["sla_known"]) == (5, 60, 3, 4)
    assert (es["tickets"], es["median_frt_min"], es["sla_met"], es["sla_known"]) == (6, 90, 3, 6)
    assert es["share"] == pytest.approx(6 / 11)


def test_speed_by_category_and_priority(report):
    lost = row(report["tables"]["frt_by_category"], "category", "card_lost_stolen")
    assert (lost["sla_met"], lost["sla_known"]) == (1, 3)      # T1 met, T8 and T10 missed
    assert lost["median_resolution_min"] == 180                 # T1 and T8, 3 h each
    urgent = row(report["tables"]["frt_by_priority"], "priority", "urgent")
    assert urgent["tickets"] == 3
    assert list(report["tables"]["frt_by_priority"]["priority"]) == ["urgent", "high", "normal", "low"]


def test_median_resolution(report):
    tickets = report["tickets"]
    assert tickets["resolution_min"].median() == 1080


def test_backlog_buckets(report):
    by_age = report["tables"]["backlog_by_age"].set_index("age")["open"].to_dict()
    assert by_age == {"under_1": 2, "1_to_3": 1, "3_to_7": 1, "7_plus": 0}
    app_bug = row(report["tables"]["backlog_by_category"], "category", "app_bug")
    assert app_bug["3_to_7"] == 1
    ages = report["tickets"].set_index("ticket_id")["age_days"]
    assert ages["T6"] == pytest.approx(4.9)
    assert ages["T9"] == pytest.approx(2.3)


def test_urgent_open_list_has_id_category_age_only(report):
    urgent = report["tables"]["urgent_open"]
    assert list(urgent.columns) == ["ticket_id", "category", "age_days"]
    assert list(urgent["ticket_id"]) == ["T10"]
    assert urgent.iloc[0]["category"] == "card_lost_stolen"


def test_satisfaction(report):
    sat = report["tables"]["satisfaction"].set_index("language")
    assert (sat.loc["en", "good"], sat.loc["en", "bad"]) == (1, 0)
    assert (sat.loc["es", "good"], sat.loc["es", "bad"]) == (1, 1)


def test_no_satisfaction_column_means_no_table():
    from helpers import csv_bytes
    df, quality = load_export(csv_bytes("ticket_id,created_at\nA,2026-10-20 10:00"))
    assert "satisfaction" not in build_report(df, quality)["tables"]


def test_default_as_of_is_the_latest_date_in_the_file():
    df, _ = load_export(str(TINY))
    assert latest_time(df).strftime("%Y-%m-%d %H:%M") == "2026-10-23 16:30"


def test_tickets_created_after_as_of_are_left_out():
    df, quality = load_export(str(TINY))
    report = build_report(df, quality, TINY_AS_OF.replace(day=16, hour=12))
    assert report["kpis"]["tickets"] == 3   # T1, T2, T3


@pytest.mark.parametrize("days,bucket", [(0, "under_1"), (0.99, "under_1"), (1, "1_to_3"),
                                         (3, "3_to_7"), (6.9, "3_to_7"), (7, "7_plus"),
                                         (None, None)])
def test_age_bucket_edges(days, bucket):
    assert age_bucket(days) == bucket

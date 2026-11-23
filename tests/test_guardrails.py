"""The tool never writes to customers, so the guardrail is: never show
sensitive text. Outputs hold counts, times, ticket IDs and categories only.
And lost cards stay urgent whatever the export says.

tests/fixtures/sensitive_export.csv is hand-written: its subjects and
descriptions hold a fake card number (starts with 0000), a CVV, one-time
codes, fake customer IDs and emails, in English and Spanish.
"""

import pytest
from helpers import SENSITIVE, csv_bytes, rendered_text, run_app

import report
from analytics.load import load_export
from analytics.metrics import build_report

SECRETS = [
    "0000", "4417", "8823", "9906", "917", "583920", "774102",   # card, CVV, codes
    "CVV", "XXXX-77", "cliente.demo", "example.com",               # customer details
    "Someone stole", "one-time code", "Me llegó", "Mi tarjeta es",  # ticket text EN/ES
    "Código raro", "Transfer pending",                              # subjects
]


def assert_clean(text, where):
    for secret in SECRETS:
        assert secret not in text, f"{secret!r} found in {where}"


@pytest.mark.parametrize("lang", ["en", "es"])
def test_no_ticket_text_in_any_report_file(tmp_path, lang):
    assert report.main([str(SENSITIVE), "--lang", lang, "--out", str(tmp_path)]) == 0
    files = list(tmp_path.iterdir())
    assert {"summary.md", "summary.html", "urgent_open.csv"} <= {f.name for f in files}
    assert len([f for f in files if f.suffix == ".csv"]) >= 9
    for path in files:
        assert_clean(path.read_text(encoding="utf-8-sig"), path.name)


@pytest.mark.parametrize("lang", ["en", "es"])
def test_no_ticket_text_in_console_output(capsys, tmp_path, lang):
    report.main([str(SENSITIVE), "--lang", lang, "--out", str(tmp_path)])
    assert_clean(capsys.readouterr().out, "console")


@pytest.mark.parametrize("lang", ["en", "es"])
def test_no_ticket_text_in_the_dashboard(lang):
    app = run_app(lang, data_path=SENSITIVE)
    assert not app.exception
    text = rendered_text(app)
    assert "S-3" in text            # the urgent open ticket is listed by ID...
    assert_clean(text, f"dashboard ({lang})")  # ...but nothing it said is


@pytest.mark.parametrize("lang,other", [("en", "Other"), ("es", "Otro")])
def test_unknown_channel_text_never_reaches_the_dashboard(tmp_path, lang, other):
    # A free-text channel cell with a fake card number in it.
    path = tmp_path / "channel_export.csv"
    path.write_text("Id,Created at,Via\n"
                    "C-1,2026-10-20 09:00,Web form card 0000123456789012\n"
                    "C-2,2026-10-20 10:00,Mail\n", encoding="utf-8")
    df, _ = load_export(str(path))
    assert list(df["channel"]) == ["other", "email"]
    app = run_app(lang, data_path=path)
    assert not app.exception
    options = app.sidebar.multiselect[0].options
    assert other in options and not any("0000" in o or "web form" in o.lower() for o in options)
    text = rendered_text(app)
    for secret in ("0000123456789012", "0000", "Web form", "web form"):
        assert secret not in text, f"{secret!r} found in dashboard ({lang})"


def test_lost_card_exported_as_low_gets_the_urgent_24_7_target():
    # Saturday 10:00, answered 11:30: zero business minutes, but 90 real
    # minutes. As "low" this would be met; as urgent (24/7, 60 min) it is missed.
    text = ("ticket_id,created_at,category,priority,first_response_at\n"
            "L-1,2026-10-24 10:00,card_lost_stolen,low,2026-10-24 11:30\n"
            "L-2,2026-10-24 10:00,Tarjeta perdida o robada,Baja,2026-10-24 10:45")
    df, quality = load_export(csv_bytes(text))
    assert list(df["priority"]) == ["urgent", "urgent"]
    assert quality["priority_raised"] == 2
    tickets = build_report(df, quality)["tickets"].set_index("ticket_id")
    assert tickets.loc["L-1", "sla"] == "missed"
    assert tickets.loc["L-2", "sla"] == "met"


def test_fraud_like_categories_never_go_below_their_floor():
    text = ("ticket_id,created_at,category,priority\n"
            "A,2026-10-20 10:00,charge_dispute,low\n"
            "B,2026-10-20 10:00,account_access,normal\n"
            "C,2026-10-20 10:00,app_bug,low")
    df, _ = load_export(csv_bytes(text))
    assert list(df["priority"]) == ["high", "high", "low"]

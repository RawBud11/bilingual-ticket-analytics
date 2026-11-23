import pytest
from helpers import TINY, csv_bytes

from analytics.load import LoadError, find_columns, load_export


def test_tiny_export_data_quality_counts():
    df, quality = load_export(str(TINY))
    assert quality["rows_read"] == 13
    assert quality["duplicates"] == 1         # T3 twice
    assert quality["bad_dates"] == 1          # T12 "23/10/2026 10:00"
    assert quality["language_filled"] == 1    # T8 blank -> detected
    assert quality["priority_raised"] == 1    # T1 lost card exported as "low"
    assert quality["uncategorized"] == 0
    assert quality["dropped_columns"] == 2    # customer_id, assignee
    assert quality["rows_used"] == 11
    assert quality["has_satisfaction"] is True
    assert list(df["ticket_id"]) == [f"T{n}" for n in range(1, 12)]


def test_spanish_category_label_and_blank_language():
    df, _ = load_export(str(TINY))
    t8 = df.set_index("ticket_id").loc["T8"]
    assert t8["category"] == "card_lost_stolen"   # "Tarjeta perdida o robada"
    assert t8["language"] == "es"                 # from "Perdí mi tarjeta..."
    t7 = df.set_index("ticket_id").loc["T7"]
    assert t7["priority"] == "high"               # "Alta"


def test_customer_ids_and_text_are_dropped_on_load():
    df, _ = load_export(str(TINY))
    for column in ("customer_id", "assignee", "subject", "body"):
        assert column not in df.columns
    assert not df.astype(str).apply(lambda s: s.str.contains("XXXX-")).any().any()


def test_lost_card_floor_applies_whatever_the_export_says():
    df, _ = load_export(str(TINY))
    t1 = df.set_index("ticket_id").loc["T1"]
    assert t1["priority"] == "urgent"
    assert bool(t1["priority_raised"]) is True


ZENDESK = """
Id,Requester,Requester id,Subject,Description,Status,Priority,Via,Created at,First reply at,Solved at,Category,Satisfaction Score
101,cliente.demo1@example.com,XXXX-0001,Card stolen,My card was stolen,Solved,Low,Mail,2026-10-19T09:00:00Z,2026-10-19T09:20:00Z,2026-10-19T11:00:00Z,Card lost or stolen,Good
102,cliente.demo2@example.com,XXXX-0002,Cobro,No reconozco un cargo,Open,High,Chat,2026-10-19T10:00:00Z,,,Disputa de cargo,
"""

SLA_TRACKER = """
Ticket ID,Created,Customer ID,Channel,Language,Subject,Category,Priority,Status,Assignee,First response,Last update,SLA due,SLA status,Last alerted
T-1001,2026-10-12 10:10,C-1586,Chat,,My card was stolen,Card lost or stolen,Urgent,Waiting on customer,Sam Demo,2026-10-12 10:25,2026-10-21 12:51,,,
T-1003,2026-10-12 11:40,C-1866,Email,Spanish,Me sacó de la cuenta,Account access,High,Resolved,Jordan Demo,2026-10-12 12:10,2026-10-12 21:51,,,
"""

SPANISH = """
ID del ticket,Fecha de creación,Canal,Idioma,Asunto,Categoría,Prioridad,Estado,Primera respuesta,Resuelto el
E-1,2026-10-20 09:00,Correo,Español,No me llega la transferencia,Transferencia fallida o pendiente,Media,Abierto,2026-10-20 10:00,
E-2,2026-10-20 11:00,Teléfono,Inglés,Fee question,Comisiones,Baja,Resuelto,2026-10-20 12:00,2026-10-20 15:00
"""


def test_zendesk_style_headers():
    df, quality = load_export(csv_bytes(ZENDESK))
    assert quality["rows_used"] == 2
    row = df.set_index("ticket_id").loc["101"]
    assert row["category"] == "card_lost_stolen" and row["priority"] == "urgent"
    assert row["channel"] == "email"  # "Mail"
    assert row["language"] == "en"
    assert str(row["first_response_at"]) == "2026-10-19 09:20:00"
    assert df.set_index("ticket_id").loc["102", "category"] == "charge_dispute"
    assert df.set_index("ticket_id").loc["102", "language"] == "es"


def test_sla_tracker_title_case_headers():
    df, quality = load_export(csv_bytes(SLA_TRACKER))
    assert quality["rows_used"] == 2
    t1 = df.set_index("ticket_id").loc["T-1001"]
    assert t1["category"] == "card_lost_stolen" and t1["language"] == "en"
    assert bool(t1["solved"]) is False   # "Waiting on customer" is still open
    t3 = df.set_index("ticket_id").loc["T-1003"]
    assert t3["language"] == "es" and bool(t3["solved"]) is True  # "Resolved"
    assert quality["dropped_columns"] == 6  # Customer ID, Assignee, Last update, SLA due, SLA status, Last alerted


def test_spanish_headers_and_values():
    df, _ = load_export(csv_bytes(SPANISH))
    e1, e2 = df.set_index("ticket_id").loc["E-1"], df.set_index("ticket_id").loc["E-2"]
    assert e1["category"] == "transfer_failed_pending"
    assert e1["priority"] == "high"          # "Media" raised to the transfer floor
    assert e1["channel"] == "email" and e1["language"] == "es"
    assert e2["channel"] == "phone" and e2["language"] == "en" and e2["priority"] == "low"
    assert bool(e2["solved"]) is True


def test_find_columns_ignores_case_accents_and_underscores():
    found = find_columns(["TICKET_ID", "Fecha de Creación", "first-response-at"])
    assert found == {"ticket_id": "TICKET_ID", "created_at": "Fecha de Creación",
                     "first_response_at": "first-response-at"}


def test_reply_before_created_is_ignored_not_trusted():
    text = "ticket_id,created_at,first_response_at\nA,2026-10-20 10:00,2026-10-19 10:00"
    df, quality = load_export(csv_bytes(text))
    assert quality["other_dates"] == 1
    assert df["first_response_at"].isna().all()


def test_unknown_category_and_language():
    text = "ticket_id,created_at,category,language\nA,2026-10-20 10:00,Crypto,fr"
    df, quality = load_export(csv_bytes(text))
    assert df.loc[0, "category"] == "uncategorized" and quality["uncategorized"] == 1
    assert df.loc[0, "language"] == "other"
    assert df.loc[0, "priority"] == "normal"


def test_excel_cp1252_file_still_loads():
    text = "ticket_id,created_at,subject\nA,2026-10-20 10:00,Perdí mi tarjeta y no sé qué hacer"
    df, _ = load_export(text.encode("cp1252"))
    assert df.loc[0, "language"] == "es"


def test_missing_columns_is_a_clear_error():
    with pytest.raises(LoadError) as error:
        load_export(csv_bytes("subject,body\nhello,world"))
    assert error.value.key == "error.missing_columns"
    assert error.value.values["columns"] == "ticket_id, created_at"


def test_no_readable_dates_is_a_clear_error():
    with pytest.raises(LoadError) as error:
        load_export(csv_bytes("ticket_id,created_at\nA,23/10/2026"))
    assert error.value.key == "error.empty"


def test_missing_file_is_a_clear_error(tmp_path):
    with pytest.raises(LoadError) as error:
        load_export(str(tmp_path / "nope.csv"))
    assert error.value.key == "error.file_not_found"

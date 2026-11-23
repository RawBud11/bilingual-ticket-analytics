"""Smoke tests for the Streamlit dashboard with AppTest (no server needed)."""

from helpers import TINY, rendered_text, run_app


def test_app_runs_in_english_with_the_sample_data():
    app = run_app("en")
    assert not app.exception
    assert app.title[0].value == "Support ticket analytics"
    assert [m.label for m in app.metric][:2] == ["Tickets", "Median first reply"]
    assert "sample file" in rendered_text(app)
    assert len(app.get("vega_lite_chart")) == 6


def test_app_runs_in_spanish():
    app = run_app("es")
    assert not app.exception
    assert app.title[0].value == "Análisis de tickets de soporte"
    text = rendered_text(app)
    assert "Tickets abiertos por antigüedad" in text
    assert "Lo que destaca" in text
    assert "What stands out" not in text


def test_channel_filter_changes_the_numbers():
    app = run_app("en", data_path=TINY)
    assert app.metric[0].value == "11"
    app.sidebar.multiselect[0].set_value(["email"]).run()
    assert not app.exception
    assert app.metric[0].value == "5"   # T1 T3 T6 T8 T10


def test_filters_with_no_rows_show_a_hint():
    app = run_app("es", data_path=TINY)
    app.sidebar.multiselect[0].set_value([]).run()
    assert not app.exception
    assert "Ningún ticket coincide" in app.warning[0].value

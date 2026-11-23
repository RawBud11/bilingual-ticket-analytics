from pathlib import Path

from analytics.sla import parse_time

PROJECT_DIR = Path(__file__).resolve().parent.parent
TINY = PROJECT_DIR / "data" / "tiny_export.csv"
SAMPLE = PROJECT_DIR / "data" / "sample_export.csv"
SENSITIVE = PROJECT_DIR / "tests" / "fixtures" / "sensitive_export.csv"

# The hand calculations for tiny_export.csv use this "as of" time (a Friday).
TINY_AS_OF = parse_time("2026-10-23 17:00")


def csv_bytes(text):
    """A small CSV export written inline in a test."""
    return text.strip().encode("utf-8")


def run_app(lang="en", data_path=None):
    """Run app.py with Streamlit's AppTest (no server, no browser)."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(PROJECT_DIR / "app.py"), default_timeout=120)
    if data_path:
        app.session_state["data_path"] = str(data_path)
    app.run()
    if lang != "en":
        app.sidebar.radio[0].set_value(lang).run()
    return app


def rendered_text(app):
    """Every piece of text and table data the app put on the page."""
    parts = []
    for kind in ("title", "caption", "markdown", "subheader", "info", "warning", "error"):
        parts += [str(element.value) for element in getattr(app, kind)]
    parts += [f"{m.label} {m.value}" for m in app.metric]
    parts += [element.value.to_csv() for element in app.dataframe]
    # Sidebar and main widgets: labels, the options shown and the raw values.
    for kind in ("radio", "multiselect", "selectbox", "date_input"):
        for widget in getattr(app, kind):
            parts.append(str(widget.label))
            parts += [str(option) for option in getattr(widget, "options", [])]
            parts.append(str(widget.value))
    for chart in app.get("vega_lite_chart"):
        # Chart data travels as Arrow tables; read them back as text.
        import pyarrow as pa  # installed with Streamlit

        # (The chart spec itself holds random dataset hashes, so it is skipped.)
        for dataset in chart.proto.datasets:
            parts.append(pa.ipc.open_stream(dataset.data.data).read_pandas().to_csv())
    return "\n".join(parts)

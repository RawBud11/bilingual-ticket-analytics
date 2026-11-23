"""Streamlit dashboard for a helpdesk CSV export, in English or Spanish.

Run:  streamlit run app.py

A thin layer: the numbers come from the same functions as report.py
(analytics/metrics.py, insights.py, present.py). Opens with the sample data;
upload your own export in the sidebar. Shows counts, times, ticket IDs and
categories only, never ticket text.
"""

import os

import streamlit as st
from dotenv import load_dotenv

import config
from analytics.insights import find_insights
from analytics.load import LoadError, load_export
from analytics.metrics import build_report, latest_time
from analytics.present import (TABLE_ORDER, insight_lines, kpi_lines, label, localize_table,
                               quality_lines, time_text)
from analytics.sla import parse_time
from analytics.strings import t

load_dotenv()
st.set_page_config(page_title="Support ticket analytics", layout="wide")

LANG_NAMES = {"en": "English", "es": "Español"}


@st.cache_data
def load_file(path):
    return load_export(path)


@st.cache_data
def load_upload(data):
    return load_export(data)


def chart_data(lang, name, table, column):
    """A localized table indexed by its first column, keeping one value column."""
    shown = localize_table(lang, name, table)
    return shown.set_index(shown.columns[0])[[shown.columns[column]]]


default_lang = os.getenv("REPORT_LANGUAGE", "en")
lang = st.sidebar.radio(
    "Language / Idioma", config.LANGUAGES_UI, format_func=LANG_NAMES.get, horizontal=True,
    index=config.LANGUAGES_UI.index(default_lang) if default_lang in config.LANGUAGES_UI else 0)

st.title(t(lang, "app.title"))
st.caption(t(lang, "app.caption"))
upload = st.sidebar.file_uploader(t(lang, "app.upload"), type="csv")

# AppTest cannot upload files, so tests point the app at another file here.
path = st.session_state.get("data_path", str(config.SAMPLE_FILE))
try:
    if upload is not None:
        df, quality = load_upload(upload.getvalue())
        st.sidebar.info(t(lang, "app.using_upload", file=upload.name))
    else:
        df, quality = load_file(path)
        if path == str(config.SAMPLE_FILE):
            st.sidebar.info(t(lang, "app.using_sample"))
except LoadError as error:
    st.error(t(lang, error.key, **error.values))
    st.stop()

as_of = parse_time(os.getenv("AS_OF", "")) or latest_time(df)
first, last = df["created_at"].min().date(), df["created_at"].max().date()
picked = st.sidebar.date_input(t(lang, "app.date_range"), value=(first, last),
                               min_value=first, max_value=last)
start, end = (picked[0], picked[-1]) if isinstance(picked, (tuple, list)) and picked else (first, last)
channels = sorted(df["channel"].unique())
chosen = st.sidebar.multiselect(t(lang, "app.channels"), channels, default=channels,
                                format_func=lambda c: label(lang, "channel", c))

days = df["created_at"].dt.date
filtered = df[(days >= start) & (days <= end) & df["channel"].isin(chosen)]
if filtered.empty:
    st.warning(t(lang, "app.no_rows"))
    st.stop()

report = build_report(filtered, quality, as_of)
insights = find_insights(report)
tables = report["tables"]

period_start, period_end = report["period"]
st.write(t(lang, "report.period", start=period_start.strftime("%Y-%m-%d"),
           end=period_end.strftime("%Y-%m-%d")) + " · "
         + t(lang, "report.as_of", as_of=time_text(report["as_of"])))

for column, (name, value) in zip(st.columns(5), kpi_lines(lang, report["kpis"])):
    column.metric(name, value)

st.subheader(t(lang, "report.insights_heading"))
st.markdown("\n".join(f"- {line}" for line in insight_lines(lang, insights)))

left, right = st.columns(2)
with left:
    st.subheader(t(lang, "table.weekly_volume"))
    weekly = localize_table(lang, "weekly_volume", tables["weekly_volume"])
    st.line_chart(weekly.set_index(weekly.columns[0]))
    st.subheader(t(lang, "table.frt_by_category"))
    st.bar_chart(chart_data(lang, "frt_by_category", tables["frt_by_category"], 3), sort=False)
    st.subheader(t(lang, "table.backlog_by_age"))
    st.bar_chart(chart_data(lang, "backlog_by_age", tables["backlog_by_age"], 1), sort=False)
with right:
    st.subheader(t(lang, "table.top_categories"))
    st.bar_chart(chart_data(lang, "top_categories", tables["top_categories"], 1), sort=False)
    st.subheader(t(lang, "table.frt_by_language"))
    st.bar_chart(chart_data(lang, "frt_by_language", tables["frt_by_language"], 4), sort=False)
    st.subheader(t(lang, "table.spanish_by_week"))
    st.line_chart(chart_data(lang, "spanish_by_week", tables["spanish_by_week"], 2))

st.subheader(t(lang, "table.urgent_open"))
if tables["urgent_open"].empty:
    st.write(t(lang, "report.no_urgent"))
else:
    st.dataframe(localize_table(lang, "urgent_open", tables["urgent_open"]), hide_index=True)

with st.expander(t(lang, "report.tables_heading")):
    for name in TABLE_ORDER:
        if name in tables and name != "urgent_open":
            st.markdown(f"**{t(lang, f'table.{name}')}**")
            st.dataframe(localize_table(lang, name, tables[name]), hide_index=True)
    if "satisfaction" not in tables:
        st.write(t(lang, "report.no_satisfaction"))

with st.expander(t(lang, "dq.title")):
    st.markdown("\n".join(f"- {line}" for line in quality_lines(lang, quality)))

st.caption(t(lang, "report.method"))
st.caption(t(lang, "report.no_text"))

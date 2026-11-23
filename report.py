"""Write a support report from a helpdesk CSV export. No Streamlit needed.

Usage:
    python report.py                                   # the sample file, English
    python report.py data/sample_export.csv --lang es
    python report.py my_export.csv --as-of "2026-10-26 08:00" --out output

Writes output/summary.md, output/summary.html and one CSV per table.
Outputs hold counts, times, ticket IDs and categories only, never ticket text.
Optional settings in .env: REPORT_LANGUAGE (en or es) and AS_OF.
"""

import argparse
import html
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

import config
from analytics.insights import find_insights
from analytics.load import LoadError, load_export
from analytics.metrics import build_report
from analytics.present import (TABLE_ORDER, insight_lines, kpi_lines, localize_table,
                               quality_lines, time_text)
from analytics.sla import parse_time
from analytics.strings import t


def make_report(source, lang, as_of=None):
    """Load, measure and put every text in `lang`. Raises LoadError."""
    df, quality = load_export(source)
    report = build_report(df, quality, as_of)
    report["insights"] = find_insights(report)
    start, end = report["period"]
    report["header"] = [
        t(lang, "report.period", start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d")),
        t(lang, "report.as_of", as_of=time_text(report["as_of"])),
    ]
    report["shown"] = {name: localize_table(lang, name, report["tables"][name])
                       for name in TABLE_ORDER if name in report["tables"]}
    return report


def cell(value):
    return "" if value is None or value != value else str(value)  # NaN != NaN


def markdown_table(table):
    lines = ["| " + " | ".join(table.columns) + " |",
             "|" + "---|" * len(table.columns)]
    for row in table.itertuples(index=False):
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    return "\n".join(lines)


def html_table(table):
    head = "".join(f"<th>{html.escape(c)}</th>" for c in table.columns)
    rows = "".join("<tr>" + "".join(f"<td>{html.escape(cell(v))}</td>" for v in row) + "</tr>"
                   for row in table.itertuples(index=False))
    return f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>"


def empty_note(lang, name):
    return {"urgent_open": t(lang, "report.no_urgent")}.get(name, "-")


def sections(report, lang, source_name, is_sample):
    """The report as (kind, content) pairs, so Markdown and HTML stay identical."""
    out = [("h1", t(lang, "report.title"))]
    if is_sample:
        out.append(("p", t(lang, "report.sample_note")))
    out += [("p", t(lang, "report.source", file=source_name))]
    out += [("p", line) for line in report["header"]]
    out += [("h2", t(lang, "report.kpi_heading")),
            ("list", [f"{name}: {value}" for name, value in kpi_lines(lang, report["kpis"])]),
            ("h2", t(lang, "report.insights_heading")),
            ("list", insight_lines(lang, report["insights"])),
            ("h2", t(lang, "dq.title")),
            ("list", quality_lines(lang, report["quality"])),
            ("h2", t(lang, "report.tables_heading"))]
    for name in TABLE_ORDER:
        out.append(("h3", t(lang, f"table.{name}")))
        table = report["shown"].get(name)
        if table is None:
            out.append(("p", t(lang, "report.no_satisfaction")))
        elif table.empty:
            out.append(("p", empty_note(lang, name)))
        else:
            out.append(("table", table))
    out += [("p", t(lang, "report.method")), ("p", t(lang, "report.no_text"))]
    return out


def to_markdown(parts):
    marks = {"h1": "# ", "h2": "## ", "h3": "### ", "p": ""}
    blocks = []
    for kind, content in parts:
        if kind == "list":
            blocks.append("\n".join(f"- {item}" for item in content))
        elif kind == "table":
            blocks.append(markdown_table(content))
        else:
            blocks.append(marks[kind] + content)
    return "\n\n".join(blocks) + "\n"


STYLE = ("body{font-family:system-ui,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem;"
         "color:#1f2933}table{border-collapse:collapse;margin:.5rem 0 1.5rem}"
         "th,td{border:1px solid #cbd2d9;padding:.3rem .6rem;text-align:left}"
         "th{background:#f0f4f8}")


def to_html(parts, lang):
    body = []
    for kind, content in parts:
        if kind == "list":
            body.append("<ul>" + "".join(f"<li>{html.escape(i)}</li>" for i in content) + "</ul>")
        elif kind == "table":
            body.append(html_table(content))
        else:
            body.append(f"<{kind}>{html.escape(content)}</{kind}>")
    title = html.escape(parts[0][1])
    return (f'<!doctype html>\n<html lang="{lang}"><head><meta charset="utf-8">'
            f"<title>{title}</title><style>{STYLE}</style></head><body>\n"
            + "\n".join(body) + "\n</body></html>\n")


def write_outputs(report, lang, out_dir, source_name, is_sample):
    """Write summary.md, summary.html and the CSV tables. Returns the paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = sections(report, lang, source_name, is_sample)
    md_path, html_path = out_dir / "summary.md", out_dir / "summary.html"
    md_path.write_text(to_markdown(parts), encoding="utf-8")
    html_path.write_text(to_html(parts, lang), encoding="utf-8")
    csv_paths = []
    for name, table in report["shown"].items():
        path = out_dir / f"{name}.csv"  # file names stay English in both languages
        table.to_csv(path, index=False, encoding="utf-8-sig")  # utf-8-sig: Excel shows accents
        csv_paths.append(path)
    return md_path, html_path, csv_paths


def shown_path(path):
    try:
        return Path(path).resolve().relative_to(Path.cwd()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):  # accents and ñ on the Windows console
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    load_dotenv()
    parser = argparse.ArgumentParser(description="Support ticket report from a CSV export (EN/ES).")
    parser.add_argument("file", nargs="?", default=str(config.SAMPLE_FILE),
                        help="helpdesk CSV export (default: data/sample_export.csv)")
    parser.add_argument("--lang", choices=config.LANGUAGES_UI,
                        default=os.getenv("REPORT_LANGUAGE") or "en")
    parser.add_argument("--as-of", default=os.getenv("AS_OF") or "",
                        help='backlog date, like "2026-10-26 08:00" (default: latest date in the file)')
    parser.add_argument("--out", default="output", help="output folder (default: output)")
    args = parser.parse_args(argv)
    lang = args.lang if args.lang in config.LANGUAGES_UI else "en"

    as_of = None
    if args.as_of:
        as_of = parse_time(args.as_of)
        if as_of is None:
            print(t(lang, "error.bad_as_of", value=args.as_of), file=sys.stderr)
            return 1
    try:
        report = make_report(args.file, lang, as_of)
    except LoadError as error:
        print(t(lang, error.key, **error.values), file=sys.stderr)
        return 1

    is_sample = Path(args.file).resolve() == config.SAMPLE_FILE.resolve()
    md_path, html_path, csv_paths = write_outputs(
        report, lang, args.out, Path(args.file).name, is_sample)

    print(t(lang, "report.title"))
    for line in report["header"]:
        print(line)
    print()
    print(t(lang, "dq.title"))
    for line in quality_lines(lang, report["quality"]):
        print(f"  {line}")
    print()
    print(t(lang, "report.kpi_heading"))
    for name, value in kpi_lines(lang, report["kpis"]):
        print(f"  {name}: {value}")
    print()
    print(t(lang, "report.insights_heading"))
    for line in insight_lines(lang, report["insights"]):
        print(f"  - {line}")
    print()
    print(t(lang, "report.wrote", path=shown_path(md_path)))
    print(t(lang, "report.wrote_csvs", count=len(csv_paths), path=shown_path(args.out)))
    print(t(lang, "report.wrote", path=shown_path(html_path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

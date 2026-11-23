import csv
import subprocess
import sys

from helpers import PROJECT_DIR, SAMPLE, TINY

import report


def test_report_writes_md_html_and_csvs(tmp_path, capsys):
    code = report.main([str(TINY), "--as-of", "2026-10-23 17:00", "--out", str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "Tickets: 11" in out
    assert "Median first reply: 1.2 h" in out
    assert "First replies within SLA: 60%" in out
    assert "Open backlog: 4" in out
    assert "Spanish share: 55%" in out
    assert "summary.html" in out
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert md.startswith("# Support ticket report")
    assert "| T10 | Card lost or stolen | 0.2 |" in md
    html = (tmp_path / "summary.html").read_text(encoding="utf-8")
    assert '<html lang="en">' in html and "<table>" in html


def test_csv_tables_are_utf8_sig_with_spanish_headers(tmp_path):
    report.main([str(TINY), "--lang", "es", "--as-of", "2026-10-23 17:00", "--out", str(tmp_path)])
    raw = (tmp_path / "backlog_by_age.csv").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # BOM, so Excel shows accents
    with open(tmp_path / "backlog_by_age.csv", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["Antigüedad", "Abiertos"]
    assert rows[1] == ["Menos de 1 día hábil", "2"]


def test_spanish_input_spanish_report_english_report_english(tmp_path, capsys):
    report.main([str(TINY), "--lang", "es", "--out", str(tmp_path / "es")])
    es = capsys.readouterr().out
    report.main([str(TINY), "--lang", "en", "--out", str(tmp_path / "en")])
    en = capsys.readouterr().out
    assert "Calidad de los datos" in es and "Data quality" not in es
    assert "Data quality" in en and "Calidad de los datos" not in en
    assert '<html lang="es">' in (tmp_path / "es" / "summary.html").read_text(encoding="utf-8")


def test_missing_file_is_a_clear_message(tmp_path, capsys):
    assert report.main([str(tmp_path / "nope.csv"), "--out", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert "File not found" in err and "Traceback" not in err


def test_bad_as_of_is_a_clear_message_in_spanish(tmp_path, capsys):
    assert report.main([str(TINY), "--lang", "es", "--as-of", "ayer", "--out", str(tmp_path)]) == 1
    assert "AS_OF debe verse así" in capsys.readouterr().err


def test_sample_report_runs_from_the_command_line(tmp_path):
    """The 60-second demo command, as a real process, in Spanish."""
    result = subprocess.run(
        [sys.executable, "report.py", "data/sample_export.csv", "--lang", "es",
         "--out", str(tmp_path)],
        cwd=PROJECT_DIR, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stderr
    assert "Calidad de los datos" in result.stdout
    assert "Porcentaje en español" in result.stdout
    assert "summary.html" in result.stdout


def test_generator_is_reproducible():
    sys.path.insert(0, str(PROJECT_DIR / "scripts"))
    import generate_data

    rows_a, rows_b = generate_data.build(42), generate_data.build(42)
    assert rows_a == rows_b
    with open(SAMPLE, encoding="utf-8-sig", newline="") as f:
        committed = list(csv.DictReader(f))
    assert committed == [{c: r[c] for c in generate_data.COLUMNS} for r in rows_a]

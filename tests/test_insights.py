import re

import pytest
from helpers import SAMPLE, TINY, TINY_AS_OF

from analytics.insights import find_insights
from analytics.load import load_export
from analytics.metrics import build_report
from analytics.present import insight_lines
from analytics.strings import STRINGS


def insights_for(path, as_of=None):
    df, quality = load_export(str(path))
    return find_insights(build_report(df, quality, as_of))


def test_tiny_export_spanish_slower():
    # Spanish median 90 min vs English 60 min = 1.5x, above the 1.25x threshold.
    found = dict(insights_for(TINY, TINY_AS_OF))
    assert found["insight.spanish_slower"]["ratio"] == 1.5
    assert "insight.spike" not in found   # 11 tickets: below the minimum size


def test_sample_data_finds_the_planted_patterns():
    found = insights_for(SAMPLE)
    keys = [key for key, _ in found]
    assert "insight.spanish_slower" in keys
    assert "insight.spanish_share_change" in keys
    spike = [values for key, values in found if key == "insight.spike"][0]
    assert spike["category"] == "transfer_failed_pending"
    assert spike["week"].strftime("%Y-%m-%d") == "2026-09-14"
    backlog = dict(found)["insight.old_backlog"]
    assert backlog["category"] == "app_bug"
    share = dict(found)["insight.spanish_share_change"]
    assert share["end"] > share["start"]


@pytest.mark.parametrize("lang", ["en", "es"])
def test_sentences_render_in_both_languages(lang):
    lines = insight_lines(lang, insights_for(SAMPLE))
    assert lines and all("{" not in line for line in lines)
    if lang == "es":
        assert any("español" in line for line in lines)


def test_nothing_found_says_so():
    assert insight_lines("es", []) == ["Nada superó los umbrales de config.py con estos datos."]


# Insight sentences describe; they never recommend, predict or promise.
BANNED = {
    "en": [r"\breduc", r"\bimprov", r"\bguarantee", r"\bpromise", r"\bshould\b",
           r"\brecommend", r"\bwill\b", r"\bsave[sd]?\b", r"\bboost", r"%\s*(less|more|faster)"],
    "es": [r"\breduc", r"\bmejor", r"\bgarantiz", r"\bpromet", r"\bdeber", r"\brecomend",
           r"\bahorr", r"\baument", r"%\s*(menos|más)"],
}


@pytest.mark.parametrize("lang", ["en", "es"])
def test_insight_templates_never_promise(lang):
    templates = [text for key, text in STRINGS[lang].items() if key.startswith("insight.")]
    assert len(templates) == 6
    for text in templates:
        for pattern in BANNED[lang]:
            assert not re.search(pattern, text, re.IGNORECASE), (pattern, text)

import re

import config
from analytics.strings import STRINGS, pct, t


def test_english_and_spanish_have_the_same_keys():
    assert set(STRINGS["en"]) == set(STRINGS["es"])


def test_same_slots_in_both_languages():
    for key, english in STRINGS["en"].items():
        slots = set(re.findall(r"{(\w+)}", english))
        assert slots == set(re.findall(r"{(\w+)}", STRINGS["es"][key])), key


def test_every_category_priority_and_language_has_a_label():
    for lang in STRINGS:
        for key in config.CATEGORIES + [config.UNCATEGORIZED]:
            assert f"category.{key}" in STRINGS[lang]
        for key in config.PRIORITIES:
            assert f"priority.{key}" in STRINGS[lang]
        for key, _, _ in config.AGE_BUCKETS:
            assert f"age.{key}" in STRINGS[lang]


def test_spanish_uses_tu_with_accents():
    spanish = " ".join(STRINGS["es"].values())
    assert "usted" not in spanish.lower()
    assert t("es", "app.upload") == "Sube tu exportación CSV"
    assert t("es", "table.backlog_by_age") == "Tickets abiertos por antigüedad"
    for word in ("categoría", "Verificación", "Teléfono", "días hábiles", "Inglés", "Español"):
        assert word in spanish


def test_labels_match_the_other_puentara_projects():
    assert t("en", "category.card_lost_stolen") == "Card lost or stolen"
    assert t("es", "category.card_lost_stolen") == "Tarjeta perdida o robada"
    assert t("es", "priority.normal") == "Media"


def test_percent_style():
    assert pct("en", 0.6) == "60%"
    assert pct("es", 0.6) == "60 %"
    assert pct("es", None) == "-"

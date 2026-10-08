"""Tests without a model for build_materi.py, generate_materi.py and the create_materi tool.

    python -m pytest research/agentic/algorithms/skills/materi_belajar/tests -q -p no:cacheprovider
"""

import copy
import json
import re
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
FIXTURES = SKILL / "tests" / "fixtures"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parent.parent))
import build_materi as bm  # noqa: E402
import generate_materi as gm  # noqa: E402
import local_model as lm  # noqa: E402
from skills.materi_belajar import materi_belajar_skill as skill  # noqa: E402

REFERENCE = json.loads((FIXTURES / "materi-reksa-dana-modul-2.json").read_text(encoding="utf-8"))


@pytest.fixture
def silabus_json(tmp_path):
    """The reference syllabus as silabus_belajar saves it (with module numbers)."""
    data = json.loads((FIXTURES / "silabus-reksa-dana.json").read_text(encoding="utf-8"))
    number = 0
    for stage in data["stages"]:
        for module in stage["modules"]:
            number += 1
            module["number"] = number
    data["money_topic"] = True
    path = tmp_path / "silabus-reksa-dana.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


def spec(**changes):
    data = copy.deepcopy(REFERENCE)
    data.update(changes)
    return data


def quiz_of(page: str) -> list:
    return json.loads(re.search(r"var QUIZ = (\[.*?\]);", page, re.S).group(1))


# ---------------------------------------------------------------------------
# A good spec becomes a lesson that follows the rules
# ---------------------------------------------------------------------------

def test_reference_lesson_builds_without_warnings(tmp_path, silabus_json):
    contract = bm.load_contract(silabus_json, 2)
    res = bm.build_materi(REFERENCE, str(tmp_path / "m.html"), contract, model="test")

    assert res["ok"] and res["warnings"] == []
    assert (res["chapters"], res["diagrams"], res["demo"], res["questions"], res["terms"]) == (4, 4, True, 5, 4)
    page = Path(res["path"]).read_text(encoding="utf-8")
    assert "Modul 2 dari 6" in page and 'href="silabus-reksa-dana.html"' in page
    assert "Berikutnya: Modul 3, Empat jenis reksa dana" in page
    assert page.count('<div class="term">') == 4 and page.count("<dt>") == 4
    assert "bukan saran keuangan" in page and "{{" not in page


def test_contract_objectives_win_over_the_models(tmp_path, silabus_json):
    contract = bm.load_contract(silabus_json, 2)
    data = spec(objectives=["Memahami NAB", "Mengetahui unit"])

    normalized, _ = bm.normalize(data, contract)

    assert normalized["objectives"] == contract["objectives"]
    assert normalized["title"] == "NAB dan cara nilai investasi berubah"


def test_right_answers_move_and_every_explanation_names_a_chapter(tmp_path):
    data = spec()
    data["quiz"][2]["why"] = "Jumlah unit hanya berubah saat membeli atau menjual."

    page = bm.render(bm.normalize(data)[0])
    quiz = quiz_of(page)

    assert [q["a"] for q in quiz] == [1, 0, 2, 2, 0]
    assert all(q["opts"][q["a"]] == data["quiz"][i]["right"] for i, q in enumerate(quiz))
    assert all(re.search(r"bab \d", q["why"]) for q in quiz)
    assert quiz[2]["why"].endswith("Lihat bab 1.")       # the first chapter that teaches objective 2


def test_options_with_an_index_are_read_too():
    data = spec()
    data["quiz"][0] = {"question": "Berapa 2 + 2?", "options": ["3", "4", "5"], "answer": 1, "why": "Lihat bab 1.",
                       "objective": 1}

    quiz = bm.normalize(data)[0]["quiz"]

    assert quiz[0]["opts"][quiz[0]["a"]] == "4" and len(quiz[0]["opts"]) == 3


def test_a_question_without_two_wrong_answers_is_dropped():
    data = spec()
    data["quiz"][1]["wrong"] = ["2.000 unit"]

    normalized, warnings = bm.normalize(data)

    assert len(normalized["quiz"]) == 4
    assert any("quiz question dropped" in w for w in warnings)


def test_untaught_and_untested_objectives_are_reported():
    data = spec(objectives=["Menghitung jumlah unit", "Menghitung untung rugi", "Membandingkan dua reksa dana"])

    _, warnings = bm.normalize(data)

    assert "objective 3 is taught by no chapter: 'Membandingkan dua reksa dana'" in warnings
    assert "objective 3 is tested by no question or exercise: 'Membandingkan dua reksa dana'" in warnings


def test_terms_from_the_card_without_a_term_box_are_reported(tmp_path, silabus_json):
    contract = bm.load_contract(silabus_json, 2)
    data = spec()
    data["chapters"][3]["terms"] = []

    _, warnings = bm.normalize(data, contract)

    assert "terms from the module card without a term box: redemption" in warnings


def test_an_empty_prior_is_written_from_the_previous_card(silabus_json):
    contract = bm.load_contract(silabus_json, 2)

    normalized, warnings = bm.normalize(spec(prior=""), contract)

    assert normalized["prior"].startswith(f"Modul sebelumnya, {contract['previous']['title']}, mengajarkan ")
    assert "prior was empty; written from the previous module card" in warnings


def test_chapter_titles_lose_the_number_the_page_already_shows():
    data = spec()
    data["chapters"][0]["title"] = "1. Menghitung jumlah unit"
    data["chapters"][1]["title"] = "Bab 2: Untung dan rugi"
    data["chapters"][2]["title"] = "3 langkah membaca NAB"

    normalized, _ = bm.normalize(data)

    assert [c["title"] for c in normalized["chapters"][:3]] == [
        "Menghitung jumlah unit", "Untung dan rugi", "3 langkah membaca NAB"]


def test_a_term_gets_one_box_at_its_first_appearance():
    data = spec()
    data["chapters"][2]["terms"] = [{"term": "NAB", "meaning": "lagi"}]

    normalized, _ = bm.normalize(data)

    assert [t["term"] for c in normalized["chapters"] for t in c["terms"]] == ["NAB", "NAB per unit", "subscription",
                                                                              "redemption"]


def test_demo_needs_three_steps():
    data = spec()
    data["demo"]["steps"] = data["demo"]["steps"][:2]

    normalized, warnings = bm.normalize(data)
    block, script = bm.demo_block(normalized["demo"])

    assert (block, script) == ("", "")
    assert any("no interactive demo" in w for w in warnings)


@pytest.mark.parametrize("text", [
    "400 x Rp1.300 = Rp520.000", "Rp500.000 / Rp1.250 = 400", "400 unit x Rp1.200 = Rp480.000", "0,5 x 10 = 5",
    "Untung Rp30.000 (600 x (Rp1.150 - Rp1.100))", "(12.000 + 8.000) x 2 = 40.000", "10 : 4 = 2,5",
    "Langkah 1: Pembelian", "df.shape menghasilkan (412, 4)", "pendapatan(3, 15000) menghasilkan 45000",
    "400 x (Rp1.300 - Rp1.250) = 400 x Rp50 = Rp20.000",                # a chain, seen from gemma3:4b
    "Perubahan = Rp480.000 - Rp500.000 = -Rp20.000", "Rp1.000.000 x 1,5% = Rp15.000",
    "Langkah 2: 400 x Rp1.300 = Rp520.000", "Rp520.000 = 400 x Rp1.300",
    "Nilai Investasi (NAB Rp1.600) = 500 x Rp1.600 = Rp800.000",
])
def test_correct_or_non_arithmetic_text_is_not_reported(text):
    assert bm.arithmetic_errors(text) == []


@pytest.mark.parametrize("text, result", [
    ("400 x Rp1.300 = Rp52.000", "520,000"),
    ("2 x 3 x 4 = 20", "24"),
    ("Untung Rp75.000 (600 x (Rp1.150 - Rp1.100))", "30,000"),          # seen from gemma3:4b
    ("nilainya Rp1.050.000 (800 - 300) x Rp1.350", "675,000"),          # seen from gemma3:4b
    ("Karena Rp39.000 = 300 x (Rp1.300 - Rp1.250)", "15,000"),          # result first, seen from gemma3:4b
    ("400 x (Rp1.300 - Rp1.250) = 400 x Rp50 = Rp25.000", "20,000"),
])
def test_wrong_written_arithmetic_is_reported_with_the_right_result(text, result):
    (error,) = bm.arithmetic_errors(text)

    assert error.endswith(f"(hasilnya {result})")


def test_arithmetic_errors_become_warnings_with_their_place():
    data = spec()
    data["exercises"][0]["expected"] = "500 unit; 500 x Rp1.650 = Rp852.000."

    _, warnings = bm.normalize(data)

    assert warnings == ["arithmetic in latihan 'Hitung dua kemungkinan' does not add up: "
                        "500 x Rp1.650 = Rp852.000 (hasilnya 825,000)"]


def test_too_few_chapters_is_an_error_the_model_can_fix():
    with pytest.raises(bm.SpecError, match="3-6 chapters"):
        bm.normalize(spec(chapters=REFERENCE["chapters"][:2]))


def test_contract_for_a_missing_module_is_refused(silabus_json):
    with pytest.raises(bm.SpecError, match="module 9"):
        bm.load_contract(silabus_json, 9)


# ---------------------------------------------------------------------------
# Generator and tool, with a fake model
# ---------------------------------------------------------------------------

def test_generator_puts_the_card_in_the_request_and_retries(tmp_path, silabus_json, monkeypatch):
    answers = iter(["bukan json", json.dumps(REFERENCE)])
    sent = []

    def fake_ask(settings, system, user, schema):
        sent.append(user)
        return next(answers), {"seconds": 1.0, "tokens": 100}

    monkeypatch.setattr(gm, "ask_model", fake_ask)
    contract = bm.load_contract(silabus_json, 2)
    res = gm.generate("", str(tmp_path / "m.html"), contract, settings=gm.Settings(model="fake"), retries=1)

    assert res["ok"] and res["attempts"] == 2
    assert "Modul 2 dari 6" in sent[0] and "1. Menghitung jumlah unit" in sent[0]
    assert "Modul sebelumnya: Apa yang Anda beli" in sent[0]
    assert "not JSON" in sent[1]


def test_strings_cut_at_the_schema_limit_are_named():
    schema = json.loads(gm.SCHEMA.read_text(encoding="utf-8"))
    data = spec()
    data["next"] = "x" * schema["properties"]["next"]["maxLength"]
    data["chapters"][1]["steps"][0] = "y" * 120

    assert gm.cut_fields(data, schema) == ["chapters[2].steps[1]", "next"]
    assert gm.cut_fields(spec(), schema) == []


def test_context_fits_the_request_unless_it_is_set():
    settings = gm.Settings(model="m", max_tokens=4608)

    assert lm.context_size(settings, "s" * 2500, "u" * 2500) == 7168      # 2000 + 4608 + 256
    assert lm.context_size(gm.Settings(model="m", num_ctx=12288), "s", "u") == 12288


def test_generator_needs_a_topic_or_a_card():
    assert gm.generate()["error"].startswith("give a topic")


def test_tool_reports_an_unreachable_server_as_a_sentence(tmp_path, monkeypatch):
    monkeypatch.setenv(skill.OUTPUT_DIR_ENV, str(tmp_path))
    monkeypatch.setattr(skill._llm, "choose_model", lambda *a, **k: "nothing")
    monkeypatch.setattr(skill._llm.Settings, "base", property(lambda self: "http://127.0.0.1:9"))

    assert skill.materi_text("Bunga majemuk").startswith("No lesson:")


@pytest.mark.parametrize("text, plain", [
    ("konsep *Net Asset Value* (NAV)", "konsep Net Asset Value (NAV)"), ("**fee** pengelolaan", "fee pengelolaan"),
    ("pakai `read_csv` lalu `df.head()`", "pakai read_csv lalu df.head()"),
    ("400 * 1.300 = 520.000", "400 * 1.300 = 520.000"), ("2*3*4 = 24", "2*3*4 = 24"), ("total_jumlah = 412", "total_jumlah = 412"),
])
def test_markdown_from_the_model_becomes_plain_text(text, plain):
    assert bm._plain(text) == plain

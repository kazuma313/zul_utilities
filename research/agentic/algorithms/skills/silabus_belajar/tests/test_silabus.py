"""Tests without a model for build_silabus.py, generate_silabus.py and the create_silabus tool.

    python -m pytest research/agentic/algorithms/skills/silabus_belajar/tests -q -p no:cacheprovider
"""

import copy
import json
import re
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parent.parent))
import build_silabus as bs  # noqa: E402
import generate_silabus as gs  # noqa: E402
from skills.silabus_belajar import silabus_belajar_skill as skill  # noqa: E402

REFERENCE = json.loads((SKILL / "tests" / "fixtures" / "silabus-reksa-dana.json").read_text(encoding="utf-8"))


def spec(**changes):
    data = copy.deepcopy(REFERENCE)
    data.update(changes)
    return data


def modules(data):
    return [m for s in data["stages"] for m in s["modules"]]


# ---------------------------------------------------------------------------
# A good spec becomes a page that follows the rules
# ---------------------------------------------------------------------------

def test_reference_spec_builds_without_warnings(tmp_path):
    res = bs.build_silabus(REFERENCE, str(tmp_path / "s.html"), hours_per_week=3, model="test")

    assert res["ok"] and res["warnings"] == []
    assert (res["modules"], res["stages"], res["hours"], res["weeks"]) == (6, 3, 16, 7)
    page = Path(res["path"]).read_text(encoding="utf-8")
    assert page.count('<article class="mod"') == 6 and page.count('data-mod="m') == 6
    assert "± 16 jam total" in page and "7 minggu, 3 jam per minggu" in page
    assert "{{" not in page and "silabus:reksa-dana" in page          # slug for the progress script
    assert "bukan saran keuangan" in page                             # money topic


def test_module_map_has_one_box_per_module_and_a_teal_project(tmp_path):
    svg = bs.module_map(bs.normalize(REFERENCE)[0])

    assert svg.count('class="bx"') == 6 and svg.count('class="bt"') == 1
    assert svg.count('marker-end="url(#ah)"') == 6                     # 5 between modules + 1 to the project
    for text in re.findall(r'class="tx"[^>]*>([^<]*)<', svg):
        assert len(text) <= 40


def test_normalised_json_keeps_the_module_cards_for_materi(tmp_path):
    res = bs.build_silabus(REFERENCE, str(tmp_path / "s.html"))
    saved = json.loads(Path(res["json"]).read_text(encoding="utf-8"))

    card = modules(saved)[1]
    assert card["number"] == 2 and card["objectives"][0].startswith("Menghitung")
    assert saved["hours_per_week"] == 4


def test_schedule_keeps_modules_whole_and_ends_with_the_project():
    rows = bs.make_schedule(bs.normalize(REFERENCE)[0], hours_per_week=4)

    assert [r["modules"] for r in rows] == ["Modul 1-2", "Modul 3-4", "Modul 5", "Modul 6", "Proyek akhir"]
    assert sum(r["hours"] for r in rows) == 16
    assert rows[-1]["result"] == "Rencana investasi pertama selesai"


# ---------------------------------------------------------------------------
# Repairs and checks for a small model's answer
# ---------------------------------------------------------------------------

def test_vague_objectives_become_checkable():
    data = spec()
    modules(data)[0]["objectives"][0] = "Memahami peran manajer investasi"
    data["outcomes"][0] = "Mempelajari jenis reksa dana"

    normalized, warnings = bs.normalize(data)

    assert modules(normalized)[0]["objectives"][0] == "Menjelaskan peran manajer investasi"
    assert normalized["outcomes"][0] == "Menjelaskan jenis reksa dana"
    assert len([w for w in warnings if "checkable verb" in w]) == 2


def test_outcomes_lose_a_leading_bisa_because_the_page_writes_it():
    data = spec()
    data["outcomes"][0] = "Bisa memahami jenis-jenis reksa dana"
    data["outcomes"][1] = "Bisa memilih reksa dana sesuai tujuan"

    normalized, warnings = bs.normalize(data)

    assert normalized["outcomes"][:2] == ["Menjelaskan jenis-jenis reksa dana", "Memilih reksa dana sesuai tujuan"]
    assert len([w for w in warnings if "checkable verb" in w]) == 1


def test_a_result_without_an_object_is_written_from_the_first_objective():
    data = spec()
    modules(data)[0]["result"] = "Bisa Menjelaskan"

    normalized, warnings = bs.normalize(data)

    first = modules(normalized)[0]
    assert first["result"] == "Bisa " + first["objectives"][0][:1].lower() + first["objectives"][0][1:].rstrip(".")
    assert "module 1: result too short; written from the first objective" in warnings


def test_hours_are_whole_and_between_one_and_three():
    data = spec()
    modules(data)[0]["hours"] = 5
    modules(data)[1]["hours"] = "1.6"

    normalized, warnings = bs.normalize(data)

    assert [m["hours"] for m in modules(normalized)][:2] == [3, 2]
    assert any("5 hours -> 3" in w for w in warnings)


def test_links_that_the_user_did_not_give_are_removed():
    data = spec(lead="Baca juga https://contoh-situs.example/reksa untuk detailnya.")
    allowed = [{"title": "OJK", "url": "https://ojk.go.id", "used_for": ""}]
    modules(data)[0]["exercise"] += " Lihat https://ojk.go.id"

    normalized, warnings = bs.normalize(data, allowed)

    assert "contoh-situs" not in normalized["lead"] and "https://ojk.go.id" in modules(normalized)[0]["exercise"]
    assert any("not in the given sources were removed" in w for w in warnings)


def test_a_term_used_before_the_module_that_teaches_it_is_reported():
    data = spec()
    modules(data)[0]["exercise"] = "Hitung NAB per unit dari portofolio Sari."

    _, warnings = bs.normalize(data)

    assert any("'NAB per unit' is taught in module 2 but already used in module 1" in w for w in warnings)


def test_money_topic_without_risk_or_business_model_is_reported():
    data = spec()
    data["stages"] = data["stages"][:1] + [{"name": "Penerapan", "modules": modules(data)[5:6]}]

    _, warnings = bs.normalize(data)

    assert "money topic without a module that covers risk" in warnings
    assert "money topic without a module on the business model or incentives" in warnings


def test_profit_alone_does_not_count_as_a_business_model_module():
    data = spec()
    data["stages"] = data["stages"][:1] + [{"name": "Penerapan", "modules": modules(data)[5:6]}]
    modules(data)[0]["objectives"][0] = "Menghitung keuntungan investasi reksa dana"

    _, warnings = bs.normalize(data)

    assert "money topic without a module on the business model or incentives" in warnings


def test_too_few_modules_is_an_error_the_model_can_fix():
    data = spec(stages=[{"name": "Fondasi", "modules": modules(REFERENCE)[:2]}])

    with pytest.raises(bs.SpecError, match="needs 4-8 modules"):
        bs.normalize(data)


def test_sources_file_lines(tmp_path):
    listing = tmp_path / "sumber.txt"
    listing.write_text("# sumber\nOJK: Reksa Dana | https://ojk.go.id/reksa-dana | modul 1-3\nhttps://idx.co.id\n",
                       encoding="utf-8")

    assert bs.read_sources(str(listing)) == [
        {"title": "OJK: Reksa Dana", "url": "https://ojk.go.id/reksa-dana", "used_for": "modul 1-3"},
        {"title": "https://idx.co.id", "url": "https://idx.co.id", "used_for": ""}]


# ---------------------------------------------------------------------------
# Generator and tool, with a fake model
# ---------------------------------------------------------------------------

def test_generator_sends_the_reason_back_and_retries(tmp_path, monkeypatch):
    answers = iter(['{"topic": "Reksa dana", "outcomes": ["a"]}', json.dumps(REFERENCE)])
    sent = []

    def fake_ask(settings, system, user, schema):
        sent.append(user)
        return next(answers), {"seconds": 1.0, "tokens": 100}

    monkeypatch.setattr(gs, "ask_model", fake_ask)
    res = gs.generate("Reksa dana", str(tmp_path / "s.html"), settings=gs.Settings(model="fake"), retries=1)

    assert res["ok"] and res["attempts"] == 2 and res["model"] == "fake"
    assert "tidak bisa dipakai" in sent[1] and "outcomes" in sent[1]
    assert "Bahasa Indonesia" in sent[0] and "3 jam" not in sent[0]


def test_only_a_money_topic_is_asked_for_a_business_model_module():
    money = gs.request_text("Reksa dana", "Pemula", "", 3, [], "")
    other = gs.request_text("Python untuk analisis data", "Pemula", "", 4, [], "")

    assert "model bisnis" in money and "risiko" in money
    assert "model bisnis" not in other


def test_generator_builds_again_from_a_saved_answer(tmp_path):
    answer = tmp_path / "jawaban.json"
    answer.write_text(json.dumps(REFERENCE), encoding="utf-8")

    res = gs.generate("Reksa dana", str(tmp_path / "s.html"), settings=gs.Settings(model="saved"), from_json=str(answer))

    assert res["ok"] and res["attempts"] == 1


def test_tool_reports_an_unreachable_server_as_a_sentence(tmp_path, monkeypatch):
    monkeypatch.setenv(skill.OUTPUT_DIR_ENV, str(tmp_path))
    monkeypatch.setattr(skill._llm, "choose_model", lambda *a, **k: "nothing")
    monkeypatch.setattr(skill._llm.Settings, "base", property(lambda self: "http://127.0.0.1:9"))

    reply = skill.silabus_text("Reksa dana")

    assert reply.startswith("No syllabus for 'Reksa dana'") and "model server" in reply


def test_markdown_emphasis_and_backticks_become_plain_text():
    data = spec()
    modules(data)[1]["objectives"][0] = "Menjelaskan konsep *Net Asset Value* dan **fee** dengan `contoh`"

    normalized, _ = bs.normalize(data)

    assert modules(normalized)[1]["objectives"][0] == "Menjelaskan konsep Net Asset Value dan fee dengan contoh"

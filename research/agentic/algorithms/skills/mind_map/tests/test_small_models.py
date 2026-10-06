"""Tests for the repairs that make this skill work with small local models.

    pytest research/agentic/algorithms/skills/mind_map/tests

No model is needed: `ask` is a scripted function.  Every reply used here is a shortened copy of what a
real model (qwen3:8b, qwen3:4b, gemma3:4b through Ollama) wrote while the skill was being tested.
"""

import argparse
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import generate_mindmap  # noqa: E402
from outline_parser import parse_mindmap, parse_outline  # noqa: E402
from outline_repair import (  # noqa: E402
    group_branches,
    last_outline_block,
    outline_problem,
    short_lines,
    shorten_texts,
    split_text,
    stepwise_outline,
    take_notes,
)

GOOD = "# Fotosintesis\n- Bahan\n  - Cahaya\n  - Air\n- Tahapan\n  - Reaksi terang\n- Hasil\n  - Glukosa\n"


class Scripted:
    """A fake model: answers in order and remembers what it was asked."""

    def __init__(self, *replies):
        self.replies, self.calls, self.thinking, self.schemas = list(replies), [], [], []

    def __call__(self, system, user, max_tokens=None, think=None, schema=None):
        self.calls.append((system, user, max_tokens))
        self.thinking.append(think)
        self.schemas.append(schema)
        return self.replies.pop(0)


def texts(node):
    return [kid["text"] for kid in node["children"]]


# ---------------------------------------------------------------------------
# last_outline_block
# ---------------------------------------------------------------------------

THINKING_ALOUD = """We need 3 to 8 main branches. The format is:
 # Root topic
 - Main branch 1

Possible branches:
 1. Goal
 2. Tools

Let me write it:

 # How an agent picks a tool
 - Goal
   - Task
   - Output
 - Tools
   - Available tools
 - Context

However, let me check the word count: every line is short.
 1. Goal has one word.
"""


def test_the_final_outline_is_taken_from_a_reply_that_thinks_aloud():
    root = parse_outline(last_outline_block(THINKING_ALOUD))["root"]

    assert root["text"] == "How an agent picks a tool"
    assert texts(root) == ["Goal", "Tools", "Context"]
    assert texts(root["children"][0]) == ["Task", "Output"]


def test_replies_without_such_a_block_are_left_alone():
    assert last_outline_block("no outline here") == "no outline here"
    assert last_outline_block("- A\n  - b\n- C\n") == "- A\n  - b\n- C\n"
    assert last_outline_block('{"root": "X", "nodes": []}') == '{"root": "X", "nodes": []}'
    assert last_outline_block("<think>plan</think>\n" + GOOD).strip() == GOOD.strip()


# ---------------------------------------------------------------------------
# repeated and crowded branches
# ---------------------------------------------------------------------------

def test_repeated_branches_are_merged_with_their_children():
    root, _, warnings = parse_mindmap("# T\n- A\n  - one\n- B\n- a\n  - two\n- B\n")

    assert texts(root) == ["A", "B"]
    assert texts(root["children"][0]) == ["one", "two"]
    assert sum("written twice" in w for w in warnings) == 2


def crowded(count=12):
    return parse_outline("# Topic\n" + "".join(f"- Branch {n}\n  - Detail {n}\n" for n in range(1, count + 1)))["root"]


def test_too_many_branches_are_grouped_by_number():
    root = crowded()
    model = Scripted("- **Early:** 1, 2, 3, 4\nGroup name: Middle: 5,6,7, 8, 2\nAlone: 9\nnot a group line\n")

    assert group_branches(root, model) is True
    assert texts(root) == ["Early", "Middle", "Branch 9", "Branch 10", "Branch 11", "Branch 12"]
    assert texts(root["children"][0]) == ["Branch 1", "Branch 2", "Branch 3", "Branch 4"]
    assert texts(root["children"][1]) == ["Branch 5", "Branch 6", "Branch 7", "Branch 8"]
    assert texts(root["children"][0]["children"][0]) == ["Detail 1"]
    assert model.calls[0][1].splitlines()[:2] == ["1. Branch 1", "2. Branch 2"]


def test_an_unusable_grouping_leaves_the_tree_alone():
    root = crowded()

    assert group_branches(root, Scripted("I cannot group these.")) is False
    assert len(root["children"]) == 12
    assert group_branches(crowded(5), Scripted()) is False       # nothing to group: the model is not asked


# ---------------------------------------------------------------------------
# sentence-long lines
# ---------------------------------------------------------------------------

LONG_ONE = "Provider model berganti, tool bertambah, penyimpan percakapan pindah dari memori ke database"
LONG_TWO = "[Perjalanan sebuah request](alur-request.md) mengikuti satu request melewati keempat layer"


def test_sentences_are_shortened_and_matched_by_number():
    root = parse_outline(f"# Arsitektur\n- Masalah\n  - {LONG_ONE}\n- Alur\n  - {LONG_TWO}\n  - Pendek\n")["root"]
    model = Scripted("2. Perjalanan request\n1) **Tepi yang cepat berubah**\n7. out of range\n")

    assert shorten_texts(root, model) == 2
    assert texts(root["children"][0]) == ["Tepi yang cepat berubah"]
    assert texts(root["children"][1]) == ["Perjalanan request", "Pendek"]
    assert model.calls[0][1] == f"1. {LONG_ONE}\n2. {LONG_TWO}"


def test_a_line_the_model_does_not_shorten_is_kept_for_the_parser():
    root = parse_outline(f"# A\n- B\n  - {LONG_ONE}\n- C\n")["root"]

    assert shorten_texts(root, Scripted(f"1. {LONG_ONE} dan seterusnya")) == 0
    assert texts(root["children"][0]) == [LONG_ONE]
    assert shorten_texts(parse_outline(GOOD)["root"], Scripted()) == 0      # nothing long: the model is not asked


# ---------------------------------------------------------------------------
# long sources
# ---------------------------------------------------------------------------

def test_long_text_is_split_at_paragraphs():
    text = "\n\n".join(f"Paragraph {n} " + "x" * 40 for n in range(10))
    parts = split_text(text, 120)

    assert len(parts) == 5
    assert all(len(part) <= 120 for part in parts)
    assert split_text("y" * 250, 100) == ["y" * 100, "y" * 100, "y" * 50]


def test_notes_are_taken_part_by_part():
    text = "\n\n".join("Section " + "x" * 90 for _ in range(4))
    model = Scripted("- one\n  - a", "<think>hm</think>- two\n  - b")
    seen = []

    assert take_notes(text, model, 200, progress=seen.append) == "- one\n  - a\n- two\n  - b"
    assert seen == ["reading part 1 of 2", "reading part 2 of 2"]


def options(**changes):
    values = dict(source="catatan_rapat.txt", branches=5, depth=3, language="Indonesian", max_chars=200,
                  long_source="notes")
    values.update(changes)
    return argparse.Namespace(**values)


def test_a_short_source_is_sent_whole_with_its_title_and_section_names():
    text = "# Arsitektur hexagonal\n\n## Empat layer\nDomain memuat aturan.\n\n## Arah dependensi\nImpor mengarah ke dalam.\n"
    model = Scripted()

    request = generate_mindmap.source_request(options(max_chars=5000), text, model)

    assert request.startswith("Central topic: Arsitektur hexagonal\nNumber of main branches: 5\n")
    assert "Sections found in the source:" in request
    assert f"SOURCE TEXT:\n<<<\n{text.strip()}" in request.replace("\n>>>", "")
    assert "A rough draft" not in request
    assert model.calls == []


def test_a_long_source_becomes_notes_instead_of_being_cut():
    text = "\n\n".join("Fakta " + "x" * 150 for _ in range(3))
    model = Scripted("- a\n  - 1", "- b\n  - 2", "- c\n  - 3")

    request = generate_mindmap.source_request(options(), text, model)

    assert "NOTES ON EACH PART:\n<<<\n- a\n  - 1\n- b\n  - 2\n- c\n  - 3\n>>>" in request
    assert request.startswith("Central topic: catatan rapat\n")
    assert len(model.calls) == 3

    cut = generate_mindmap.source_request(options(long_source="cut"), text, Scripted())
    assert "SOURCE TEXT:" in cut and len(cut) < len(text) + 400


def test_the_language_of_an_indonesian_or_english_source_is_named_in_the_request():
    indonesian = "Agent ini berhenti dan menunggu keputusan dari manusia, karena tool yang dipakai tidak boleh berjalan sendiri."
    english = "The agent stops and waits for a decision, because the tool is not allowed to run on its own and that is the rule."
    default = generate_mindmap.DEFAULT_LANGUAGE

    assert generate_mindmap.guess_language(indonesian) == "Indonesian"
    assert generate_mindmap.guess_language(english) == "English"
    assert generate_mindmap.guess_language("get_weather send_email ToolMessage") is None
    assert "Language: Indonesian\n" in generate_mindmap.source_request(
        options(language=default, max_chars=5000), indonesian * 3, Scripted())
    assert "Language: Japanese\n" in generate_mindmap.source_request(
        options(language="Japanese", max_chars=5000), indonesian * 3, Scripted())


def test_code_and_diagrams_are_kept_out_of_the_request():
    text = ("# Bentuk graph\n\nGraph ini punya satu node tambahan untuk persetujuan manusia.\n\n"
            "```mermaid\nflowchart LR\n    I --> F\n```\n\n## Alur\n\nNode berhenti dan menunggu.\n\n"
            "```python\ndef tool_node(state):\n    return state\n```\n")

    request = generate_mindmap.source_request(options(max_chars=5000), text, Scripted())

    assert "I --> F" not in request and "def tool_node" not in request
    assert "Node berhenti dan menunggu." in request


# ---------------------------------------------------------------------------
# repair(): what generate_mindmap.py does with a reply
# ---------------------------------------------------------------------------

def test_a_good_reply_is_passed_on_untouched_and_the_model_is_not_asked_again():
    model, notes = Scripted(), []

    assert generate_mindmap.repair(GOOD, model, notes).strip() == GOOD.strip()
    assert notes == [] and model.calls == []


def test_a_crowded_reply_with_sentences_is_grouped_then_shortened():
    raw = "# Topic\n" + "".join(f"- Branch {n}\n" for n in range(1, 11)) + f"  - {LONG_ONE}\n"
    model, notes = Scripted("First: 1, 2, 3, 4, 5\nSecond: 6, 7, 8, 9, 10", "1. Tepi yang berubah"), []

    root = parse_outline(generate_mindmap.repair(raw, model, notes))["root"]

    assert texts(root) == ["First", "Second"]
    assert texts(root["children"][1]["children"][-1]) == ["Tepi yang berubah"]
    assert notes == ["10 main branches -> grouped into 2 by the model",
                     "1 sentence-long lines -> shortened by the model"]


@pytest.mark.parametrize("raw", ['{"root": "X", "nodes": [{"text": "a"}]}', "nothing useful"])
def test_json_and_non_outlines_are_left_to_the_parser(raw):
    assert generate_mindmap.repair(raw, Scripted(), []) == raw


# ---------------------------------------------------------------------------
# is it a mind map at all?
# ---------------------------------------------------------------------------

REASONING = """# Okay, let's tackle this query. The user wants a mind map outline in Indonesian based on the source
- Looking at the source text, the sections mentioned are
- Kenapa keputusan divalidasi sebelum resume
- Wait, the user says "Number of main branches: 6". The source text has more sections. Let me check.
- Let me try to group the source into 6 main branches.
"""

LOPSIDED = """# Cara kerja human-in-the-loop
- Aksi berisiko perlu validasi manusia
- Agent berhenti sebelum menjalankan tool
- Node review di antara LLM dan tool
- Dua request untuk satu aksi
- Interrupt menghentikan graph
  - Checkpoint menyimpan state
  - Node dijalankan ulang
  - Validasi keputusan sebelum resume
  - Keputusan diterapkan setelah persetujuan
"""


def problem(text):
    return outline_problem(parse_outline(text)["root"])


def test_a_good_outline_has_no_problem():
    assert problem(GOOD) == ""


def test_reasoning_drawn_as_a_map_is_recognised():
    assert problem(REASONING) == "the central topic is a sentence"
    assert "lines are sentences" in problem("# Topik\n" + "- Ini adalah kalimat panjang yang disalin begitu saja dari sumbernya\n" * 4)


def test_a_map_with_one_branch_holding_everything_is_recognised():
    assert problem(LOPSIDED) == "4 of 5 main branches have no sub points"
    assert problem("# T\n- A\n") == "fewer than 4 nodes"
    assert problem("# T\n- A\n  - b\n  - c\n  - d\n") == "fewer than 2 main branches"


# ---------------------------------------------------------------------------
# step by step
# ---------------------------------------------------------------------------

def test_short_lines_keeps_phrases_and_drops_prose():
    reply = ("Okay, here are the branches:\n1. **Bentuk graph**\n- Dua request\n- dua request\n"
             "Wait, the user asked for six.\n### Batas langkah.\nIni adalah kalimat yang terlalu panjang untuk sebuah cabang\n")

    assert short_lines(reply, 5) == ["Bentuk graph", "Dua request", "Batas langkah"]
    assert short_lines(reply, 2) == ["Bentuk graph", "Dua request"]


def test_the_outline_is_put_together_from_branch_names_and_their_points():
    model = Scripted("Bahan\nTahapan\nHasil", "- Cahaya matahari\n- Air", "Reaksi terang\nSiklus Calvin\nTahapan",
                     "1. Glukosa\n2. Oksigen")
    seen = []

    outline = stepwise_outline("Fotosintesis", "Tumbuhan membuat makanan sendiri.", model, branches=5,
                               language="Indonesian", sections=["Bahan", "Hasil"], progress=seen.append)

    assert outline == ("# Fotosintesis\n- Bahan\n  - Cahaya matahari\n  - Air\n- Tahapan\n  - Reaksi terang\n"
                       "  - Siklus Calvin\n- Hasil\n  - Glukosa\n  - Oksigen\n")
    first, second = model.calls[0][1], model.calls[1][1]
    assert first.startswith("MATERIAL:\n<<<\nTumbuhan membuat makanan sendiri.\n>>>\n\nCentral topic: Fotosintesis\n")
    assert "Sections of the material: Bahan; Hasil\nLanguage: Indonesian\nName 3 to 5 main branches" in first
    assert "Branch: Bahan\nLanguage: Indonesian\nList 2 to 4 key points of this branch, taken from the material." in second
    assert seen == ["branch 1 of 3: Bahan", "branch 2 of 3: Tahapan", "branch 3 of 3: Hasil"]
    assert model.thinking == [None] * 4


def test_a_model_that_only_answers_after_thinking_is_asked_again_with_thinking():
    model = Scripted("Okay, let me think about the branches of this topic first.", "Bahan\nHasil",
                     "Cahaya\nAir", "Glukosa\nOksigen")

    outline = stepwise_outline("Fotosintesis", "", model)

    assert outline == "# Fotosintesis\n- Bahan\n  - Cahaya\n  - Air\n- Hasil\n  - Glukosa\n  - Oksigen\n"
    assert model.thinking == [None, "auto", None, None]
    assert model.calls[0][1].startswith("Central topic: Fotosintesis\nName 4 to 6 main branches")
    assert stepwise_outline("X", "", Scripted("no", "still nothing")) == ""


# ---------------------------------------------------------------------------
# write_outline(): one answer, again, step by step
# ---------------------------------------------------------------------------

def run_options(**changes):
    values = dict(steps="auto", retries=1, think="off", branches=6)
    values.update(changes)
    return argparse.Namespace(**values)


PLAN = {"user": "Topic: Fotosintesis", "title": "Fotosintesis", "material": "", "sections": [], "language": ""}


def test_a_usable_first_answer_is_the_only_request():
    model = Scripted(GOOD)

    outline, notes, why = generate_mindmap.write_outline(run_options(), "SYSTEM", PLAN, model)

    assert (outline.strip(), notes, why) == (GOOD.strip(), [], "")
    assert len(model.calls) == 1


def test_the_second_attempt_lets_a_thinking_only_model_think():
    model = Scripted(REASONING, GOOD)

    outline, _, why = generate_mindmap.write_outline(run_options(), "SYSTEM", PLAN, model)

    assert (outline.strip(), why) == (GOOD.strip(), "")
    assert model.thinking == [None, "auto"]
    assert "not a usable outline" in model.calls[1][1]


def test_two_unusable_answers_lead_to_the_step_by_step_outline():
    model = Scripted(REASONING, LOPSIDED, "Bahan\nHasil", "Cahaya\nAir", "Glukosa\nOksigen")

    outline, notes, why = generate_mindmap.write_outline(run_options(), "SYSTEM", PLAN, model)

    assert why == ""
    assert outline == "# Fotosintesis\n- Bahan\n  - Cahaya\n  - Air\n- Hasil\n  - Glukosa\n  - Oksigen\n"
    assert notes == ["outline built step by step (4 of 5 main branches have no sub points)"]


def test_steps_always_skips_the_single_answer_and_never_keeps_the_problem():
    always = Scripted("Bahan\nHasil", "Cahaya\nAir", "Glukosa\nOksigen")
    outline, notes, why = generate_mindmap.write_outline(run_options(steps="always"), "SYSTEM", PLAN, always)
    assert (why, notes, len(always.calls)) == ("", ["outline built step by step"], 3)

    never = Scripted(REASONING, REASONING)
    _, _, why = generate_mindmap.write_outline(run_options(steps="never"), "SYSTEM", PLAN, never)
    assert why == "the central topic is a sentence"


AS_JSON = ('{"root": "Fotosintesis", "nodes": [{"text": "Bahan", "children": [{"text": "Cahaya"}, {"text": "Air"}]}, '
           '{"text": "Tahapan", "children": [{"text": "Reaksi terang"}, {"text": "Reaksi gelap"}]}, '
           '{"text": "Hasil", "children": [{"text": "Glukosa"}, {"text": "Oksigen"}]}]}')


def test_a_model_that_needs_reasoning_is_asked_for_schema_held_json_first():
    model = Scripted(AS_JSON)

    outline, notes, why = generate_mindmap.write_outline(run_options(think="on", schema_first=True), "SYSTEM", PLAN, model)

    assert why == "" and len(model.calls) == 1 and "schema" in notes[0]
    assert outline.splitlines()[:3] == ["# Fotosintesis", "- Bahan", "  - Cahaya"]
    assert model.thinking == ["off"] and model.schemas == [generate_mindmap.OUTLINE_SCHEMA]
    assert model.calls[0][0] == generate_mindmap.JSON_SYSTEM


def test_an_unusable_schema_answer_falls_back_to_the_usual_stages():
    model = Scripted("{}", GOOD)

    outline, notes, why = generate_mindmap.write_outline(run_options(think="on", schema_first=True), "SYSTEM", PLAN, model)

    assert (outline.strip(), notes, why) == (GOOD.strip(), [], "")
    assert model.schemas == [generate_mindmap.OUTLINE_SCHEMA, None]
    assert generate_mindmap.outline_from_json("not json") == "" and generate_mindmap.outline_from_json("[1]") == ""


def test_an_empty_answer_is_a_problem_not_json():
    assert generate_mindmap.problem_of("") == "the model answered nothing"
    assert generate_mindmap.problem_of("<think>only reasoning</think>") == "the model answered nothing"
    assert generate_mindmap.repair("", Scripted(), []) == ""
    assert last_outline_block("   ") == "   "

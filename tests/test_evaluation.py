import csv
import json

import numpy as np
import pytest

from zul.evaluation import hits, latency
from zul.evaluation.config import JudgeConfig, MilvusSettings, RedisSettings, mask
from zul.evaluation.dataset import (
    as_text_list,
    describe_dataset,
    load_qa_dataset,
    load_results,
    read_table,
    save_results,
)
from zul.evaluation.generation import ChatGenerator, format_contexts
from zul.evaluation.indexing import embed_records, redis_schema, to_vector_bytes
from zul.evaluation.reports import (
    EvalReport,
    compare_reports,
    save_report,
    summarize_scores,
)
from zul.evaluation.retrievers import (
    FunctionRetriever,
    MilvusRetriever,
    RedisRetriever,
    embed_vector,
    fuse,
)
from zul.evaluation.runner import length_summary, run_rag
from zul.utilities.ranking import reciprocal_rank_fusion

# --------------------------------------------------------------------------
# Data Buatan
# --------------------------------------------------------------------------

CORPUS = {
    "mistika": [
        "Mistika adalah ajaran kebatinan.",
        "Dialektika membahas pertentangan.",
    ],
    "engels": ["Engels membedakan idealis dan materialis.", "Teks lain."],
}


def corpus_retriever(name="palsu"):
    def search(query, k):
        for key, texts in CORPUS.items():
            if key in query.lower():
                return texts[:k]
        return ["tidak ada"]

    return FunctionRetriever(search, name=name)


class EchoGenerator:
    name = "gema"

    def answer(self, question, contexts):
        return f"jawaban untuk {question} dari {len(contexts)} konteks"


class FakeEmbedding:
    def __init__(self, vector):
        self.vector = vector


class FakeEmbedder:
    def embed(self, text):
        return FakeEmbedding([float(len(text)), 1.0])


@pytest.fixture
def qa_csv(tmp_path):
    path = tmp_path / "qa.csv"
    path.write_text(
        "question,answer,law\n"
        "Apa itu mistika?,Mistika adalah ajaran kebatinan.,madilog\n"
        "Bagaimana Engels membedakan filsuf?,Lewat sejarah dan praktik.,madilog\n"
        ",tanpa pertanyaan,madilog\n",
        encoding="utf-8",
    )
    return path


# --------------------------------------------------------------------------
# Dataset
# --------------------------------------------------------------------------


def test_load_qa_dataset_maps_columns_and_skips_rows_without_question(qa_csv):
    rows = load_qa_dataset(qa_csv)

    assert len(rows) == 2
    assert rows[0] == {
        "user_input": "Apa itu mistika?",
        "reference": "Mistika adalah ajaran kebatinan.",
        "reference_contexts": None,
        "file_name": "madilog",
        "dataset": "qa",
    }
    assert describe_dataset(rows)["per_dataset"] == {"qa": 2}


def test_load_qa_dataset_reports_missing_columns_and_accepts_column_map(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("tanya,jawab\na,b\n", encoding="utf-8")

    with pytest.raises(ValueError, match="user_input"):
        load_qa_dataset(path)
    rows = load_qa_dataset(
        path, column_map={"Tanya": "user_input", "jawab": "reference"}
    )
    assert rows[0]["reference"] == "b"


def test_load_qa_dataset_needs_a_file():
    with pytest.raises(ValueError, match="minimal satu"):
        load_qa_dataset()


def test_reference_contexts_become_text_lists(tmp_path):
    path = tmp_path / "x.json"
    path.write_text(
        json.dumps(
            [
                {"question": "q", "ground_truth": "a", "context": '["k1", "k2"]'},
                {"question": "q2", "ground_truth": "a2", "context": "satu"},
                {"question": "q3", "ground_truth": "a3", "context": ["x", ""]},
            ]
        ),
        encoding="utf-8",
    )

    rows = load_qa_dataset(path)

    assert [row["reference_contexts"] for row in rows] == [
        ["k1", "k2"],
        ["satu"],
        ["x"],
    ]


def test_as_text_list_reads_json_python_repr_and_empty_cells():
    assert as_text_list("['a', 'b']") == ["a", "b"]
    assert as_text_list('["a"]') == ["a"]
    assert as_text_list("") is None
    assert as_text_list(float("nan")) is None
    assert as_text_list("[bukan list") == ["[bukan list"]


def test_read_table_reads_jsonl_and_rejects_unknown_formats(tmp_path):
    path = tmp_path / "qa.jsonl"
    path.write_text('{"question": "q"}\n\n{"question": "r"}\n', encoding="utf-8")

    assert read_table(path) == [{"question": "q"}, {"question": "r"}]
    with pytest.raises(ValueError, match="tidak didukung"):
        read_table(tmp_path / "qa.txt")


def test_read_table_reads_the_first_excel_sheet(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["question", "answer", None])
    sheet.append(["Apa itu mistika?", "Ajaran kebatinan.", "catatan"])
    sheet.append([None, None, None])
    path = tmp_path / "qa.xlsx"
    workbook.save(path)

    assert read_table(path) == [
        {
            "question": "Apa itu mistika?",
            "answer": "Ajaran kebatinan.",
            "kolom_3": "catatan",
        }
    ]
    assert load_qa_dataset(path)[0]["user_input"] == "Apa itu mistika?"


@pytest.mark.parametrize("suffix", [".csv", ".jsonl"])
def test_save_results_and_load_results_keep_lists_and_numbers(tmp_path, suffix):
    rows = [
        {
            "user_input": "q",
            "retrieved_contexts": ["a", 'kutip "dua"'],
            "response": "",
            "reference": "r",
            "reference_contexts": None,
            "top_k": 5,
        }
    ]

    path = save_results(rows, tmp_path / "out" / f"hasil{suffix}")
    loaded = load_results(path)

    assert loaded[0]["retrieved_contexts"] == ["a", 'kutip "dua"']
    assert loaded[0]["reference_contexts"] is None
    assert loaded[0]["top_k"] == 5
    assert loaded[0]["response"] == ""


def test_load_results_reads_old_pandas_csv(tmp_path):
    path = tmp_path / "lama.csv"
    path.write_text(
        ",user_input,retrieved_contexts,response,reference\n0,q,\"['a', 'b']\",,ref\n",
        encoding="utf-8",
    )

    rows = load_results(path)

    assert rows == [
        {
            "user_input": "q",
            "retrieved_contexts": ["a", "b"],
            "response": "",
            "reference": "ref",
        }
    ]


def test_csv_results_can_hold_very_long_contexts(tmp_path):
    long_text = "x" * 200_000
    path = save_results(
        [{"user_input": "q", "retrieved_contexts": [long_text]}], tmp_path / "o.csv"
    )

    assert load_results(path)[0]["retrieved_contexts"] == [long_text]


def test_save_results_rejects_other_formats(tmp_path):
    with pytest.raises(ValueError, match=".csv atau .jsonl"):
        save_results([], tmp_path / "hasil.xlsx")


# --------------------------------------------------------------------------
# Retriever Dan Generator
# --------------------------------------------------------------------------


class FakeRedisDB:
    def __init__(self):
        self.calls = []

    def text_search(self, *args, **kwargs):
        self.calls.append(("text", args, kwargs))
        return [{"content": "teks"}]

    def vector_search(self, *args, **kwargs):
        self.calls.append(("vector", args, kwargs))
        return [{"content": "vektor"}]

    def hybrid_search(self, *args, **kwargs):
        self.calls.append(("hybrid", args, kwargs))
        return [{"content": "hybrid"}]

    def hybrid_search_rrf(self, *args, **kwargs):
        self.calls.append(("rrf", args, kwargs))
        return [("a", 0.1), ("b", 0.05)], ["a", "b", "c"]


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("text", ["teks"]),
        ("vector", ["vektor"]),
        ("hybrid", ["hybrid"]),
        ("rrf", ["a", "b"]),
    ],
)
def test_redis_retriever_calls_the_search_for_its_mode(mode, expected):
    db = FakeRedisDB()
    retriever = RedisRetriever(db, FakeEmbedder(), mode=mode, alpha=0.3, rrf_k=10)

    assert retriever.retrieve("tanya", top_k=2) == expected
    assert retriever.name == f"redis-{mode}"
    called, args, kwargs = db.calls[0]
    assert called == mode
    assert kwargs["num_results"] == 2
    if mode == "hybrid":
        assert kwargs["alpha"] == 0.3
    if mode == "rrf":
        assert kwargs["rrf_K"] == 10
    if mode != "text":
        assert args[0 if mode == "vector" else 1] == [5.0, 1.0]


def test_redis_retriever_rejects_unknown_modes():
    with pytest.raises(ValueError, match="tidak dikenal"):
        RedisRetriever(FakeRedisDB(), FakeEmbedder(), mode="semantik")


def test_milvus_retriever_reads_the_first_result_list():
    class FakeStore:
        def hybrid_search(self, collection, **kwargs):
            self.kwargs = {"collection": collection, **kwargs}
            return [[{"entity": {"content": "satu"}}, {"entity": {"content": "dua"}}]]

    store = FakeStore()
    retriever = MilvusRetriever(store, FakeEmbedder(), collection="koleksi", rrf_k=7)

    assert retriever.retrieve("tanya", top_k=1) == ["satu"]
    assert store.kwargs["rrf_k"] == 7
    assert store.kwargs["query_vector"] == [5.0, 1.0]


def test_function_retriever_trims_to_top_k_and_fuse_ranks_shared_items_first():
    retriever = FunctionRetriever(lambda query, k: ["a", "b", "c"])

    assert retriever.retrieve("q", top_k=2) == ["a", "b"]
    assert fuse(["a", "b", "c"], ["b", "d"], k=1)[0] == "b"


def test_embed_vector_accepts_objects_and_plain_lists():
    class ListEmbedder:
        def embed(self, text):
            return [1, 2]

    assert embed_vector(FakeEmbedder(), "abc") == [3.0, 1.0]
    assert embed_vector(ListEmbedder(), "abc") == [1.0, 2.0]


def test_chat_generator_formats_prompt_and_trims_contexts():
    class FakeModel:
        def chat(self, prompt):
            self.prompt = prompt

            class Reply:
                content = "  jawaban  "

            return Reply()

    model = FakeModel()
    generator = ChatGenerator(model, max_context_chars=12)

    assert generator.answer("Apa?", ["konteks pertama", "kedua"]) == "jawaban"
    assert "Konteks:\n[1] konteks \n\nPertanyaan: Apa?" in model.prompt
    assert format_contexts([" a ", "b"]) == "[1] a\n\n[2] b"


# --------------------------------------------------------------------------
# Menjalankan RAG
# --------------------------------------------------------------------------


def test_run_rag_writes_while_running_and_resumes(qa_csv, tmp_path):
    rows = load_qa_dataset(qa_csv)
    out = tmp_path / "hasil.csv"

    results = run_rag(
        rows,
        corpus_retriever(),
        EchoGenerator(),
        top_k=1,
        out_path=out,
        show_progress=False,
    )

    assert results[0]["retrieved_contexts"] == ["Mistika adalah ajaran kebatinan."]
    assert results[0]["response"].startswith("jawaban untuk")
    assert (results[0]["retriever"], results[0]["generator"]) == ("palsu", "gema")
    assert load_results(out)[1]["retrieved_contexts"] == [
        "Engels membedakan idealis dan materialis."
    ]

    def explode(query, k):
        raise RuntimeError("tidak boleh dipanggil")

    resumed = run_rag(
        rows, FunctionRetriever(explode), top_k=1, out_path=out, show_progress=False
    )
    assert len(resumed) == 2
    assert length_summary(resumed)["konteks_kosong"] == 0


def test_run_rag_without_generator_leaves_response_empty(qa_csv):
    results = run_rag(
        load_qa_dataset(qa_csv), corpus_retriever(), top_k=2, show_progress=False
    )

    assert all(row["response"] == "" for row in results)
    assert all(row["generator"] == "" for row in results)


def test_run_rag_keeps_the_same_question_from_two_datasets(tmp_path, qa_csv):
    copy = tmp_path / "qa2.csv"
    copy.write_text(qa_csv.read_text(encoding="utf-8"), encoding="utf-8")
    rows = load_qa_dataset(qa_csv, copy)
    out = tmp_path / "hasil.jsonl"

    run_rag(rows, corpus_retriever(), out_path=out, show_progress=False)
    resumed = run_rag(rows, corpus_retriever(), out_path=out, show_progress=False)

    assert [row["dataset"] for row in resumed] == ["qa", "qa", "qa2", "qa2"]


def test_length_summary_of_empty_results():
    assert length_summary([]) == {"jumlah": 0, "konteks_kosong": 0}


# --------------------------------------------------------------------------
# Index
# --------------------------------------------------------------------------


def test_redis_schema_has_text_and_vector_fields():
    schema = redis_schema("idx", prefix="doc", dims=4, algorithm="flat")

    assert schema["index"] == {"name": "idx", "prefix": "doc", "storage_type": "hash"}
    assert schema["fields"][1]["attrs"]["dims"] == 4
    assert schema["fields"][1]["attrs"]["algorithm"] == "flat"


def test_embed_records_writes_bytes_or_lists_and_records_durations():
    durations = []
    records = [{"content": "abc", "source": "a.pdf"}]

    as_bytes = embed_records(
        records, FakeEmbedder(), durations=durations, show_progress=False
    )
    as_list = embed_records(
        records, FakeEmbedder(), as_bytes=False, show_progress=False
    )

    vector = np.frombuffer(as_bytes[0]["content_embedding_vector"], dtype=np.float32)
    assert vector.tolist() == [3.0, 1.0]
    assert as_list[0]["content_embedding_vector"] == [3.0, 1.0]
    assert as_list[0]["source"] == "a.pdf"
    assert len(durations) == 1
    assert "content_embedding_vector" not in records[0]
    assert to_vector_bytes([1, 2]) == np.array([1, 2], dtype=np.float32).tobytes()


def test_chunking_per_page_and_recursive(monkeypatch, tmp_path):
    documents = pytest.importorskip("zul.evaluation.documents")
    monkeypatch.setattr(
        documents, "read_pdf_pages", lambda path: ["halaman satu " * 20, "", "dua"]
    )
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.PDF").write_bytes(b"")
    (tmp_path / "a.pdf").write_bytes(b"")

    pages = documents.chunk_per_page(tmp_path / "a.pdf")
    pieces = documents.chunk_recursive(tmp_path / "a.pdf", chunk_size=60, overlap=0)
    every_pdf = documents.chunk_folder(tmp_path, strategy="per_page")

    assert [chunk.page for chunk in pages] == [1, 3]
    assert len(pieces) > 1 and all(len(c.content) <= 60 for c in pieces)
    assert len(every_pdf) == 4
    assert documents.find_pdfs(tmp_path)[1].name == "b.PDF"
    assert documents.chunks_to_records(pages[:1], text_field="text")[0]["text"]
    assert documents.length_stats(pages)["jumlah"] == 2
    with pytest.raises(ValueError, match="tidak dikenal"):
        documents.chunk_folder(tmp_path, strategy="kalimat")
    with pytest.raises(FileNotFoundError):
        documents.find_pdfs(tmp_path / "tidak-ada")


def test_milvus_store_builds_hybrid_collection_and_searches(monkeypatch):
    pymilvus = pytest.importorskip("pymilvus")
    from zul.adapters import milvus as milvus_adapter
    from zul.evaluation.milvus_store import MilvusHybridStore

    class FakeClient:
        create_schema = staticmethod(pymilvus.MilvusClient.create_schema)
        prepare_index_params = staticmethod(pymilvus.MilvusClient.prepare_index_params)

        def __init__(self, **connection):
            self.connection = connection
            self.databases, self.collections, self.calls = ["default"], {}, []

        def list_databases(self):
            return self.databases

        def create_database(self, db_name):
            self.databases.append(db_name)

        def use_database(self, db_name):
            self.calls.append(("use", db_name))

        def list_collections(self):
            return list(self.collections)

        def create_collection(self, collection_name, schema, index_params, shards_num):
            self.collections[collection_name] = schema

        def insert(self, **kwargs):
            self.calls.append(("insert", len(kwargs["data"])))

        def hybrid_search(self, **kwargs):
            self.calls.append(("hybrid", kwargs))
            return [[{"entity": {"content": "hasil"}}]]

        def drop_collection(self, collection_name):
            del self.collections[collection_name]

    monkeypatch.setattr(milvus_adapter, "MilvusClient", FakeClient)
    store = MilvusHybridStore(
        MilvusSettings(uri="http://milvus", port=1, db_name="eval")
    )

    assert store.client.connection["uri"] == "http://milvus:1"
    assert ("use", "eval") in store.client.calls
    assert store.ensure_collection("koleksi", dims=3) is True
    assert store.ensure_collection("koleksi", dims=3) is False
    schema = store.client.collections["koleksi"]
    assert [f.name for f in schema.fields] == [
        "id",
        "content",
        "content_embedding_vector",
        "content_embedding_sparse",
    ]
    assert store.insert("koleksi", [{"content": "a"}] * 5, batch_size=2) == 5
    assert [call for call in store.client.calls if call[0] == "insert"] == [
        ("insert", 2),
        ("insert", 2),
        ("insert", 1),
    ]
    hits_found = store.hybrid_search("koleksi", "tanya", [0.1, 0.2, 0.3], limit=2)
    assert hits_found[0][0]["entity"]["content"] == "hasil"
    search = store.client.calls[-1][1]
    assert [request.anns_field for request in search["reqs"]] == [
        "content_embedding_vector",
        "content_embedding_sparse",
    ]
    store.drop_collection("koleksi")
    assert store.client.collections == {}


# --------------------------------------------------------------------------
# Skor Tanpa LLM, Laporan, Dan Latensi
# --------------------------------------------------------------------------


def test_hit_stats_use_reference_answers_when_there_are_no_reference_contexts(qa_csv):
    results = run_rag(
        load_qa_dataset(qa_csv), corpus_retriever(), top_k=2, show_progress=False
    )

    stats = hits.retrieval_hit_stats(results)

    # Hanya jawaban acuan mistika yang termuat di konteksnya.
    assert stats == {
        "n": 2,
        "hit_rate": 0.5,
        "mrr": 0.5,
        "threshold": 0.6,
        "sumber": "reference",
    }


def test_hit_stats_use_reference_contexts_when_present():
    results = [
        {
            "user_input": "q",
            "retrieved_contexts": ["salah", "Ini konteks yang benar sekali."],
            "reference": "x",
            "reference_contexts": ["Ini   KONTEKS yang benar sekali."],
        }
    ]

    stats = hits.retrieval_hit_stats(results)

    assert (stats["hit_rate"], stats["mrr"], stats["sumber"]) == (
        1.0,
        0.5,
        "reference_contexts",
    )
    assert hits.similarity("", "a") == 0.0
    assert hits.first_hit_rank(["a"], ["zzz"]) is None


def test_reports_are_saved_summarized_and_compared(tmp_path):
    rows = [
        {"user_input": "q", "context_recall": 0.5},
        {"user_input": "r", "context_recall": None},
    ]
    report = EvalReport(
        name="a",
        metrics=["context_recall", "faithfulness"],
        summary=summarize_scores(rows, ["context_recall", "faithfulness"]),
        rows=rows,
        meta={"n": 2},
    )
    old = tmp_path / "lama.scores.json"
    old.write_text(
        json.dumps(
            {
                "name": "lama",
                "summary": {"context_recall": 0.2},
                "meta": {"jumlah_baris": 9},
            }
        ),
        encoding="utf-8",
    )

    json_path, csv_path = save_report(report, tmp_path)

    assert report.summary == {"context_recall": 0.5, "faithfulness": None}
    assert "faithfulness=-" in repr(report)
    assert csv_path.exists()
    assert compare_reports(json_path, old) == [
        {"name": "a", "context_recall": 0.5, "faithfulness": None, "n": 2},
        {"name": "lama", "context_recall": 0.2, "n": 9},
    ]


def test_measure_latency_counts_every_call_and_summarizes():
    stats = latency.measure_latency(
        lambda x: x, [1, 2, 3], repeats=2, workers=2, label="uji"
    )

    assert (stats.calls, stats.label) == (6, "uji")
    assert stats.qps > 0
    summary = latency.summarize_times([0.1, 0.2, 0.3, 0.4], label="x")
    assert (summary.p50, summary.max, summary.qps) == (0.3, 0.4, 4.0)
    assert latency.summarize_times([]).calls == 0


def test_save_times_csv_allows_series_of_different_lengths(tmp_path):
    path = latency.save_times_csv(
        {"a": [0.1, 0.2], "b": [0.3]}, tmp_path / "t" / "lat.csv"
    )

    with path.open(encoding="utf-8") as file:
        assert list(csv.reader(file)) == [["a", "b"], ["0.1", "0.3"], ["0.2", ""]]


def test_reciprocal_rank_fusion_is_shared_with_the_redis_helper():
    scored, ranked = reciprocal_rank_fusion(["a", "b"], ["b", "c"], K=1)

    assert ranked[0] == "b"
    assert dict(scored)["b"] == pytest.approx(1 / 3 + 1 / 2)


# --------------------------------------------------------------------------
# Pengaturan
# --------------------------------------------------------------------------

JUDGE_VARIABLES = (
    "RAGAS_JUDGE_MODEL",
    "RAGAS_JUDGE_API_KEY",
    "RAGAS_JUDGE_BASE_URL",
    "RAGAS_EMBEDDING_MODEL",
    "RAGAS_EMBEDDING_API_KEY",
    "RAGAS_EMBEDDING_BASE_URL",
    "OPENAI_API_KEY",
)


@pytest.fixture
def clean_judge_env(monkeypatch):
    for name in JUDGE_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_judge_config_falls_back_to_openai_key_and_masks_it(clean_judge_env):
    clean_judge_env.setenv("OPENAI_API_KEY", "sk-rahasia-1234")
    clean_judge_env.setenv("RAGAS_JUDGE_BASE_URL", "http://vllm:8000/v1")

    config = JudgeConfig.from_env().validate()

    assert config.embedding_api_key == "sk-rahasia-1234"
    assert config.embedding_base_url == "http://vllm:8000/v1"
    assert "rahasia" not in json.dumps(config.safe_summary())
    assert config.safe_summary()["api_key"] == "…1234"
    assert mask(None) == "(kosong)"


def test_judge_config_without_key_is_rejected(clean_judge_env):
    with pytest.raises(ValueError, match="RAGAS_JUDGE_API_KEY"):
        JudgeConfig.from_env().validate()


def test_redis_settings_from_url_hide_the_password(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://:p%40ss%21@10.0.0.5:6006/2")

    settings = RedisSettings.from_env()

    assert (settings.host, settings.port, settings.password, settings.db) == (
        "10.0.0.5",
        6006,
        "p@ss!",
        2,
    )
    assert "p@ss!" not in json.dumps(settings.safe_summary())


def test_milvus_settings_from_env(monkeypatch):
    monkeypatch.setenv("MILVUS_URI", "http://milvus")
    monkeypatch.setenv("MILVUS_PORT", "19531")

    assert MilvusSettings.from_env().address == "http://milvus:19531"

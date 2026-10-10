from importlib.util import find_spec

import pytest

# ragas hanya bisa diimpor lewat adapter Zul, yang menambal satu impor ragas
# yang rusak. Jadi di sini yang diperiksa apakah paket ragas ter-install.
if find_spec("ragas") is None:
    pytest.skip("butuh extra evaluation", allow_module_level=True)

from zul.adapters import ragas as ragas_adapter  # noqa: E402
from zul.evaluation import judge  # noqa: E402
from zul.evaluation.config import JudgeConfig  # noqa: E402

CONFIG = JudgeConfig(model="gpt-4o-mini", api_key="sk-uji-1234")


def result(response="", reference_contexts=None, retriever="redis-rrf"):
    return {
        "user_input": "Apa itu mistika?",
        "retrieved_contexts": ["Mistika adalah ajaran kebatinan.", "lain"],
        "response": response,
        "reference": "Mistika adalah ajaran kebatinan.",
        "reference_contexts": reference_contexts,
        "retriever": retriever,
        "generator": "",
        "top_k": 2,
    }


# --------------------------------------------------------------------------
# Memilih Metrik Dan Menyusun Sampel
# --------------------------------------------------------------------------


def test_metrics_that_need_a_response_are_skipped_without_answers():
    chosen, skipped = judge.select_metrics([result()], judge.DEFAULT_METRICS)

    assert chosen == ["context_precision", "context_recall"]
    assert skipped == ["faithfulness", "answer_relevancy"]


def test_unknown_or_unrunnable_metrics_are_rejected():
    with pytest.raises(ValueError, match="tidak dikenal"):
        judge.select_metrics([result()], ["ngawur"])
    with pytest.raises(ValueError, match="Tidak ada metrik"):
        judge.select_metrics([result()], judge.GENERATION_METRICS)


def test_samples_carry_response_and_reference_contexts_only_when_present():
    plain, answered = judge.to_samples([result(), result("jawaban", ["acuan"])])

    assert set(plain) == {"user_input", "retrieved_contexts", "reference"}
    assert answered["response"] == "jawaban"
    assert answered["reference_contexts"] == ["acuan"]
    with pytest.raises(ValueError, match="reference_contexts"):
        judge.to_samples([result()], need_reference_contexts=True)


# --------------------------------------------------------------------------
# Evaluasi
# --------------------------------------------------------------------------


def test_nonllm_metrics_run_through_ragas_without_a_judge():
    rows = [
        result(reference_contexts=["Mistika adalah ajaran kebatinan."]),
        {
            **result(reference_contexts=["Engels membedakan idealis dan materialis."]),
            "retrieved_contexts": ["tidak relevan"],
        },
    ]

    report = judge.evaluate_rag(rows, judge.NONLLM_METRICS, show_progress=False)

    assert report.name == "redis-rrf"
    assert report.metrics == ["context_precision_nonllm", "context_recall_nonllm"]
    assert report.summary["context_recall_nonllm"] == pytest.approx(0.5)
    assert report.rows[1]["context_recall_nonllm"] == 0.0
    assert report.meta["n"] == 2
    assert report.meta["judge"] is None


def test_evaluate_rag_builds_judges_from_config_and_passes_them_to_ragas(monkeypatch):
    calls = {}
    monkeypatch.setattr(judge, "make_judge", lambda config, backend: f"llm:{backend}")
    monkeypatch.setattr(judge, "make_judge_embeddings", lambda config: "embedding")

    def fake_evaluate(samples, metrics, llm=None, embeddings=None, **options):
        calls.update(metrics=metrics, llm=llm, embeddings=embeddings, options=options)
        return [{name: None if name == "faithfulness" else 0.8 for name in metrics}]

    monkeypatch.setattr(ragas_adapter, "evaluate", fake_evaluate)

    report = judge.evaluate_rag(
        [result("jawaban")],
        judge.DEFAULT_METRICS,
        name="uji",
        judge_config=CONFIG,
        judge_backend="langchain",
        timeout=30,
    )

    assert calls["metrics"] == list(judge.DEFAULT_METRICS)
    assert (calls["llm"], calls["embeddings"]) == ("llm:langchain", "embedding")
    assert calls["options"]["timeout"] == 30
    assert report.summary["faithfulness"] is None
    assert report.summary["context_recall"] == 0.8
    assert report.meta["judge"]["api_key"] == "…1234"


def test_evaluate_rag_reads_results_from_a_file(tmp_path, monkeypatch):
    from zul.evaluation.dataset import save_results

    path = save_results([result()], tmp_path / "hasil.csv")
    monkeypatch.setattr(
        ragas_adapter,
        "evaluate",
        lambda samples, metrics, **kwargs: [{name: 1.0 for name in metrics}],
    )

    report = judge.evaluate_rag(path, ["context_recall"], judge="llm-sendiri")

    assert report.summary == {"context_recall": 1.0}
    assert report.meta["top_k"] == 2


def test_evaluate_rag_rejects_empty_results():
    with pytest.raises(ValueError, match="kosong"):
        judge.evaluate_rag([], judge="llm")


# --------------------------------------------------------------------------
# Model Penilai Dan Adapter
# --------------------------------------------------------------------------


def test_make_judge_builds_instructor_and_langchain_judges():
    instructor_llm = judge.make_judge(CONFIG)
    langchain_llm = judge.make_judge(CONFIG, backend="langchain")

    assert instructor_llm.is_async
    assert type(langchain_llm).__name__ == "LangchainLLMWrapper"
    with pytest.raises(ValueError, match="Backend"):
        judge.make_judge(CONFIG, backend="ngawur")
    with pytest.raises(ValueError, match="Kunci model penilai"):
        judge.make_judge(JudgeConfig())


def test_judge_embeddings_have_the_method_answer_relevancy_calls():
    embeddings = judge.make_judge_embeddings(
        JudgeConfig(
            embedding_api_key="sk-uji", embedding_model="text-embedding-3-small"
        )
    )

    assert hasattr(embeddings, "embed_query")
    assert hasattr(embeddings, "embed_documents")
    with pytest.raises(ValueError, match="embedding penilai"):
        judge.make_judge_embeddings(JudgeConfig())


def test_every_known_metric_has_a_ragas_class():
    assert set(ragas_adapter.METRIC_CLASSES) == set(judge.KNOWN_METRICS)
    for name in judge.KNOWN_METRICS:
        assert ragas_adapter.metric(name) is not None
    with pytest.raises(ValueError, match="tidak dikenal"):
        ragas_adapter.metric("ngawur")

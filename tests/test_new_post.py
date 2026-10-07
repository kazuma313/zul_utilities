import importlib.util
import shutil
from datetime import date
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent

# scripts/ bukan package, jadi modulnya dimuat langsung dari path filenya.
spec = importlib.util.spec_from_file_location(
    "new_post", ROOT / "scripts" / "new_post.py"
)
new_post = importlib.util.module_from_spec(spec)
spec.loader.exec_module(new_post)

DAY = date(2026, 10, 7)


@pytest.fixture
def blog_dir(tmp_path):
    """Folder blog sementara yang memakai template asli dari docs/blog."""
    blog = tmp_path / "blog"
    blog.mkdir()
    shutil.copy(ROOT / "docs" / "blog" / "_template.md", blog / "_template.md")
    return blog


def front_matter(text: str) -> dict:
    _, header, _ = text.split("---", 2)
    return yaml.safe_load(header)


# --------------------------------------------------------------------------
# slugify
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("title", "slug"),
    [
        ("Memilih Model Lokal", "memilih-model-lokal"),
        ("RAG: hasil & catatan!", "rag-hasil-catatan"),
        ("Café résumé", "cafe-resume"),
        ("  qwen3:8b vs gemma3:4b  ", "qwen3-8b-vs-gemma3-4b"),
        ("!!!", ""),
    ],
)
def test_slugify_makes_a_lowercase_ascii_file_name(title, slug):
    assert new_post.slugify(title) == slug


def test_slugify_cuts_long_titles_without_a_trailing_hyphen():
    slug = new_post.slugify("kata " * 30)

    assert len(slug) <= new_post.MAX_SLUG_LENGTH
    assert not slug.endswith("-")


# --------------------------------------------------------------------------
# create_post
# --------------------------------------------------------------------------


def test_create_post_writes_the_post_and_its_resource_folder(blog_dir):
    post, resources = new_post.create_post("Belajar BM25", DAY, ["RAG"], blog_dir)

    assert post == blog_dir / "posts" / "2026-10-07-belajar-bm25.md"
    assert resources == blog_dir / "resources" / "2026-10-07-belajar-bm25"
    assert resources.is_dir()


def test_created_post_has_the_date_title_categories_and_summary_marker(blog_dir):
    post, _ = new_post.create_post("Belajar BM25", DAY, ["RAG", "Python"], blog_dir)
    text = post.read_text(encoding="utf-8")
    meta = front_matter(text)

    assert meta["date"]["created"] == DAY
    assert meta["categories"] == ["RAG", "Python"]
    assert meta["authors"] == ["kurnia"]
    assert "# Belajar BM25" in text
    assert "<!-- more -->" in text
    assert "resources/2026-10-07-belajar-bm25/" in text
    assert "{{" not in text


def test_category_with_a_colon_stays_valid_yaml(blog_dir):
    post, _ = new_post.create_post("Catatan", DAY, ["LLM: lokal #1"], blog_dir)

    assert front_matter(post.read_text(encoding="utf-8"))["categories"] == [
        "LLM: lokal #1"
    ]


def test_create_post_uses_today_and_the_default_category(blog_dir):
    post, _ = new_post.create_post("Tanpa opsi", blog_dir=blog_dir)
    meta = front_matter(post.read_text(encoding="utf-8"))

    assert post.name.startswith(date.today().isoformat())
    assert meta["categories"] == [new_post.DEFAULT_CATEGORY]


def test_create_post_refuses_to_overwrite_a_post(blog_dir):
    new_post.create_post("Belajar BM25", DAY, blog_dir=blog_dir)

    with pytest.raises(FileExistsError):
        new_post.create_post("Belajar BM25", DAY, blog_dir=blog_dir)


def test_create_post_rejects_a_title_without_letters(blog_dir):
    with pytest.raises(ValueError):
        new_post.create_post("???", DAY, blog_dir=blog_dir)


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------


def test_main_rejects_a_date_in_the_wrong_format(capsys):
    with pytest.raises(SystemExit) as exit_info:
        new_post.main(["Judul", "--tanggal", "07-10-2026"])

    assert exit_info.value.code == 2
    assert "YYYY-MM-DD" in capsys.readouterr().err

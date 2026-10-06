"""
Command untuk install utilities secara lokal di project

Gunanya:
    Menulis file config awal yang valid untuk helper vector database,
    supaya tidak perlu menyalin contoh config dari dokumentasi.

Cara pakai:
    zul install milvus-helper                              # milvus_config.json
    zul install redis-helper                               # redis_config.yaml
    zul install milvus-helper --config-name milvus.yaml    # format mengikuti ekstensi
    zul install milvus-helper --force                      # timpa tanpa bertanya

Setelah itu, sesuaikan isi file lalu pakai di Python:
    from zul.utilities.vector_DB.milvus_helper import MilvusHelper

    milvus = MilvusHelper(config_path="milvus_config.json")

Cara menambah perintah install untuk helper lain:
    Buat dict config default (harus lolos validasi skema helper-nya), lalu
    panggil `_write_config(DEFAULT_CONFIG, config_name, overwrite)`.
"""

import json
from pathlib import Path
from typing import Any

import typer
import yaml

app = typer.Typer(
    no_args_is_help=True, help="Tulis file config utilitas ke folder proyek"
)

YAML_SUFFIXES = (".yaml", ".yml")
JSON_SUFFIXES = (".json",)

# --------------------------------------------------------------------------
# Konfigurasi Awal Milvus
# --------------------------------------------------------------------------
#
# Isi awal ini sudah lolos validasi skema MilvusHelper, jadi file yang
# ditulis bisa langsung dimuat tanpa diubah. Satu collection contoh
# disertakan supaya bentuk field dan index-nya langsung terlihat.
#

DEFAULT_MILVUS_CONFIG: dict[str, Any] = {
    "connection": {
        "uri": "http://localhost",
        "port": 19530,
        "db_name": "default",
    },
    "collections": [
        {
            "collection_name": "my_collection",
            "shards_num": 2,
            "description": "My first collection",
            "milvus_schema": {
                "auto_id": True,
                "enable_dynamic_field": True,
                "fields": [
                    {
                        "field_name": "id",
                        "datatype": "VARCHAR",
                        "max_length": 128,
                        "is_primary": True,
                    },
                    {
                        "field_name": "embedding",
                        "datatype": "FLOAT_VECTOR",
                        "dim": 768,
                    },
                ],
                "functions": [],
            },
            "indexes": [
                {
                    "field_name": "embedding",
                    "index_name": "emb_idx",
                    "index_type": "HNSW",
                    "metric_type": "COSINE",
                    "params": {"M": 16, "efConstruction": 200},
                }
            ],
        }
    ],
}

# --------------------------------------------------------------------------
# Konfigurasi Awal Redis
# --------------------------------------------------------------------------
#
# Isi awal ini sudah lolos validasi skema RedisHelper. Kunci index
# ditulis sebagai schema, sama seperti di contoh file config, dan
# bagian hybrid_search berisi nilai bawaan untuk pencarian.
#

DEFAULT_REDIS_CONFIG: dict[str, Any] = {
    "connection": {
        "uri": "http://localhost",
        "port": 6379,
    },
    "schema": {
        "index": {
            "name": "my_index",
            "prefix": "doc",
            "storage_type": "hash",
        },
        "fields": [
            {"name": "content", "type": "text"},
            {
                "name": "content_embedding_vector",
                "type": "vector",
                "attrs": {
                    "dims": 768,
                    "distance_metric": "cosine",
                    "algorithm": "flat",
                    "datatype": "float32",
                },
            },
        ],
    },
    "hybrid_search": {
        "text_field_name": "content",
        "vector_field_name": "content_embedding_vector",
        "text_scorer": "BM25",
        "alpha": 0.5,
        "num_results": 10,
        "return_fields": ["content"],
    },
}


# --------------------------------------------------------------------------
# Menulis File Config
# --------------------------------------------------------------------------


def _serialize_config(config: dict[str, Any], config_file: Path) -> str:
    """Format config sebagai YAML atau JSON, mengikuti ekstensi file."""
    suffix = config_file.suffix.lower()

    if suffix in YAML_SUFFIXES:
        return yaml.safe_dump(config, sort_keys=False, allow_unicode=True)

    if suffix in JSON_SUFFIXES:
        return json.dumps(config, indent=4) + "\n"

    raise typer.BadParameter(
        f"Format '{config_file.suffix}' tidak didukung. Pakai .json, .yaml, atau .yml"
    )


def _write_config(config: dict[str, Any], config_name: str, overwrite: bool) -> Path:
    """
    Tulis config ke folder project saat ini (cwd).
    Jika file sudah ada, minta konfirmasi kecuali overwrite=True.
    """
    config_file = Path.cwd() / config_name
    content = _serialize_config(config, config_file)

    if config_file.exists() and not overwrite:
        typer.secho(
            f"⚠️  {config_file.name} sudah ada di folder project!",
            fg=typer.colors.YELLOW,
        )
        if not typer.confirm("Ganti konfigurasi lama?", default=False):
            typer.echo("⏹️  Dibatalkan.")
            raise typer.Exit(0)

    config_file.write_text(content, encoding="utf-8")
    typer.secho(f"✅ {config_file} berhasil dibuat!", fg=typer.colors.GREEN)

    typer.echo("\n📁 File config:")
    typer.echo(f"  - {config_file}")

    return config_file


# --------------------------------------------------------------------------
# Perintah
# --------------------------------------------------------------------------
#
# Setiap perintah terdaftar dengan dua nama. Nama bertanda hubung
# adalah nama resminya, sedangkan nama bergaris bawah adalah
# nama lama yang tetap diterima tetapi tidak ditampilkan.
#


@app.command("milvus-helper")
@app.command("milvus_helper", hidden=True)
def milvus_helper(
    config_name: str = typer.Option(
        "milvus_config.json", help="Nama file config (.json, .yaml, atau .yml)"
    ),
    overwrite: bool = typer.Option(
        False, "--force", "-f", help="Timpa file config yang sudah ada tanpa bertanya"
    ),
):
    """
    Inisialisasi konfigurasi milvus_helper di folder project saat ini.
    """
    typer.echo("📦 Setup milvus_helper config di folder project...")
    config_file = _write_config(DEFAULT_MILVUS_CONFIG, config_name, overwrite)

    typer.echo(
        "💡 Sesuaikan connection & collections di file tersebut, lalu pakai di Python:"
    )
    typer.echo("  from zul.utilities.vector_DB.milvus_helper import MilvusHelper")
    typer.echo(f"  milvus = MilvusHelper(config_path='{config_file.name}')")
    typer.echo("  milvus.list_collections()")
    typer.echo("📦 Butuh dependency: pip install 'zul[milvus]'")


@app.command("redis-helper")
@app.command("redis_helper", hidden=True)
def redis_helper(
    config_name: str = typer.Option(
        "redis_config.yaml", help="Nama file config (.json, .yaml, atau .yml)"
    ),
    overwrite: bool = typer.Option(
        False, "--force", "-f", help="Timpa file config yang sudah ada tanpa bertanya"
    ),
):
    """
    Inisialisasi konfigurasi redis_helper di folder project saat ini.
    """
    typer.echo("📦 Setup redis_helper config di folder project...")
    config_file = _write_config(DEFAULT_REDIS_CONFIG, config_name, overwrite)

    typer.echo(
        "💡 Sesuaikan connection & schema di file tersebut, lalu pakai di Python:"
    )
    typer.echo("  from zul.utilities.vector_DB.redis_helper import RedisHelper")
    typer.echo(f"  redis_helper = RedisHelper(config_path='{config_file.name}')")
    typer.echo("  redis_helper.hybrid_search(query_text='...', query_vector=[...])")
    typer.echo("📦 Butuh dependency: pip install 'zul[redis]'")

"""
Daftar fitur yang bisa dicoba di playground.

Gunanya:
    Satu tempat untuk mendaftarkan agent yang ingin dicoba. Setiap fitur
    hanya butuh nama, keterangan, dan fungsi yang merakit agent-nya.

Cara menambah fitur yang sedang kamu buat:
    1. Tulis fungsi tanpa argumen yang mengembalikan graph ter-compile.
       Rakit dengan checkpointer supaya percakapan bisa berlanjut.

        @lru_cache
        def build_rag_agent():
            return build_react_agent(
                llm=get_llm_model(),
                tools=[search_documents],
                checkpointer=get_checkpointer(),
            )

    2. Tambahkan ke `FEATURES`:

        Feature(
            name="RAG dokumen",
            description="Agent yang mencari jawaban di dokumen internal.",
            build_agent=build_rag_agent,
            examples=("Apa isi kebijakan cuti?",),
        )

    3. Jalankan ulang aplikasi, lalu muat ulang halaman Playground di
       dokumentasi. Fiturmu muncul di daftar pilihannya.

Fitur bawaan memakai agent yang sama dengan yang dilayani REST API, jadi
yang kamu coba di playground adalah yang diterima client.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.interface.http.controllers import (
    chat_controller,
    hitl_controller,
    subagents_controller,
)

# --------------------------------------------------------------------------
# Bentuk Satu Fitur
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Feature:
    """
    Satu fitur yang bisa dicoba.

    `build_agent` baru dipanggil saat fiturnya dipilih, jadi fitur yang
    belum bisa dirakit (misalnya API key belum diisi) tidak menghalangi
    fitur lain. `examples` tampil sebagai tombol pesan siap kirim.
    """

    name: str
    description: str
    build_agent: Callable[[], Any]
    examples: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# Fitur yang Tersedia
# --------------------------------------------------------------------------
#
# Urutan di daftar ini adalah urutan tampil di playground. Fitur pertama
# langsung terpilih saat halaman dibuka, jadi taruh fitur yang sedang
# kamu kerjakan di paling atas selama fitur itu masih dikembangkan.
#

FEATURES = [
    Feature(
        name="ReAct",
        description="Agent dasar dengan tool cuaca. Sama dengan `POST /chat`.",
        build_agent=chat_controller.get_react_agent,
        examples=("What is the weather in sf?",),
    ),
    Feature(
        name="Human-in-the-loop",
        description=(
            "Agent yang meminta persetujuanmu sebelum mengirim email. "
            "Sama dengan `POST /hitl/chat`."
        ),
        build_agent=hitl_controller.get_human_in_the_loop_agent,
        examples=("Kirim email ke alice@example.com: rapat besok jam 10",),
    ),
    Feature(
        name="Subagents",
        description=(
            "Supervisor yang membagi tugas ke subagent cuaca dan email. "
            "Sama dengan `POST /subagents/chat`."
        ),
        build_agent=subagents_controller.get_supervisor_agent,
        examples=("Cek cuaca di sf, lalu email hasilnya ke alice@example.com",),
    ),
]


def find_feature(name: str) -> Feature:
    """Cari fitur dari namanya."""
    for feature in FEATURES:
        if feature.name == name:
            return feature

    available = ", ".join(feature.name for feature in FEATURES)

    raise KeyError(f"Fitur '{name}' tidak terdaftar. Yang tersedia: {available}")

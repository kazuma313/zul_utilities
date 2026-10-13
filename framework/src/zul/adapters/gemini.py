"""
Adapter google-genai: client Gemini, unggah file, dan meminta teks dari model.

Gunanya:
    Satu-satunya file Zul yang mengimpor google.genai. File yang diunggah
    keluar sebagai UploadedFile berisi nama, URI, dan MIME type, dan
    jawaban model keluar sebagai teks biasa. Butuh extra gemini:
    `pip install "zul[gemini]"`.

Cara pakai:
    from zul.adapters import gemini as gemini_adapter

    client = gemini_adapter.create_client(api_key="API_KEY")
    uploaded = gemini_adapter.upload_file(client, "dokumen.pdf")
    try:
        text = gemini_adapter.generate_text(
            client, "gemini-2.5-pro", "Extract the text as markdown.", uploaded
        )
    finally:
        gemini_adapter.delete_file(client, uploaded.name)

Client dari `create_client` adalah genai.Client dan dipakai sebagai handle.
Fungsi di sini tidak menangkap error; error dari SDK atau server
Gemini diteruskan ke pemanggil apa adanya.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

# --------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------


def create_client(api_key: str) -> Any:
    """Client Gemini untuk `api_key`. Pembuatannya tidak menghubungi server.

    Objek yang dikembalikan hanya untuk diteruskan ke fungsi di file ini.
    """
    return genai.Client(api_key=api_key)


# --------------------------------------------------------------------------
# File Dan Jawaban Model
# --------------------------------------------------------------------------
#
# File diunggah lebih dulu, lalu dirujuk lewat URI dan MIME type-nya dalam
# request ke model. Cara ini sama dengan yang dilakukan SDK google-genai
# ketika objek File miliknya diletakkan langsung di dalam contents.
#


@dataclass(frozen=True)
class UploadedFile:
    """File yang sudah ada di server Gemini; `name` dipakai untuk menghapusnya."""

    name: str | None
    uri: str | None
    mime_type: str | None


def upload_file(client: Any, path: str) -> UploadedFile:
    """Unggah satu file lokal ke server Gemini."""
    uploaded = client.files.upload(file=path)
    return UploadedFile(
        name=uploaded.name, uri=uploaded.uri, mime_type=uploaded.mime_type
    )


def generate_text(
    client: Any, model: str, prompt: str, file: UploadedFile
) -> str | None:
    """Jawaban teks model untuk `prompt` beserta satu file yang sudah diunggah.

    Mengembalikan None jika jawaban model tidak berisi teks.

    Raises:
        ValueError: file tidak punya URI atau MIME type.
    """
    if not file.uri or not file.mime_type:
        raise ValueError("file uri and mime_type are required.")
    part = types.Part.from_uri(file_uri=file.uri, mime_type=file.mime_type)
    response = client.models.generate_content(model=model, contents=[prompt, part])
    return response.text


def delete_file(client: Any, name: str | None) -> None:
    """Hapus file yang sudah diunggah dari server Gemini."""
    client.files.delete(name=name)

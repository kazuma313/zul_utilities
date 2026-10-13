"""
Adapter Docling: mengubah dokumen menjadi Markdown, teks, atau dict lewat VLM.

Gunanya:
    Satu-satunya file Zul yang mengimpor docling. Opsi pipeline VLM, opsi
    deskripsi gambar, dan DocumentConverter dirakit di sini dari nilai
    biasa: URL endpoint, nama model, prompt, dan angka. Hasil konversi
    diekspor menjadi teks atau dict lewat fungsi export_*. Butuh extra
    ocr: `pip install "zul[ocr]"`.

Cara pakai:
    from zul.adapters import docling as docling_adapter

    converter = docling_adapter.create_converter(
        url="https://HOST/v1/chat/completions",
        model="NAMA_MODEL",
        prompt="Convert this page to markdown.",
        response_format="markdown",
        api_key="API_KEY",
    )
    result = docling_adapter.convert(converter, "dokumen.pdf")
    markdown = docling_adapter.export_markdown(result)

Converter dari `create_converter` dipakai sebagai handle. Hasil `convert`
adalah ConversionResult milik Docling, dan objek itu sengaja diteruskan
apa adanya, sebab DoclingVLMConverter.convert() mengembalikannya ke
pengguna, misalnya untuk membaca tabel di `result.document.tables`.
"""

from __future__ import annotations

from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PictureDescriptionApiOptions,
    VlmPipelineOptions,
)
from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions, ResponseFormat
from docling.document_converter import (
    AsciiDocFormatOption,
    CsvFormatOption,
    DocumentConverter,
    HTMLFormatOption,
    ImageFormatOption,
    MarkdownFormatOption,
    PdfFormatOption,
    PowerpointFormatOption,
    WordFormatOption,
)
from docling.pipeline.vlm_pipeline import VlmPipeline

# --------------------------------------------------------------------------
# Format Respons
# --------------------------------------------------------------------------
#
# Kunci ditulis dengan huruf kecil, nilai berupa ResponseFormat Docling.
# ResponseFormat adalah enum turunan str, jadi ResponseFormat.MARKDOWN
# sama dengan teks "markdown" saat dibandingkan dengan teks biasa.
#

RESPONSE_FORMATS: dict[str, ResponseFormat] = {
    "doctags": ResponseFormat.DOCTAGS,
    "markdown": ResponseFormat.MARKDOWN,
    "deepseek_markdown": ResponseFormat.DEEPSEEKOCR_MARKDOWN,
    "html": ResponseFormat.HTML,
    "otsl": ResponseFormat.OTSL,
    "plaintext": ResponseFormat.PLAINTEXT,
}


def find_response_format(name: str) -> ResponseFormat:
    """ResponseFormat untuk sebuah kunci RESPONSE_FORMATS atau nilai Docling.

    Raises:
        ValueError: `name` bukan kunci RESPONSE_FORMATS dan bukan nilai
            ResponseFormat yang dikenal Docling.
    """
    if name in RESPONSE_FORMATS:
        return RESPONSE_FORMATS[name]
    return ResponseFormat(name)


# --------------------------------------------------------------------------
# Membuat Converter
# --------------------------------------------------------------------------
#
# PDF dan gambar diproses pipeline VLM: setiap halaman dikirim ke model.
# DOCX, PPTX, HTML, AsciiDoc, CSV, dan Markdown dibaca dengan pembaca
# bawaan Docling untuk formatnya, dengan opsi pipeline yang sama.
#


def _auth_headers(api_key: str) -> dict[str, str]:
    """Header Authorization Bearer, atau dict kosong jika `api_key` kosong."""
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def create_converter(
    url: str,
    model: str,
    prompt: str,
    response_format: str,
    api_key: str = "",
    picture_prompt: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    skip_special_tokens: bool = False,
    timeout: int = 90,
    scale: float = 2.0,
    enable_picture_description: bool = False,
) -> Any:
    """DocumentConverter yang mengirim halaman ke endpoint chat completions.

    `url` adalah URL lengkap endpoint yang kompatibel dengan OpenAI, dan
    `response_format` sebuah kunci RESPONSE_FORMATS atau ResponseFormat.
    Jika `enable_picture_description` bernilai True, gambar di dokumen
    dideskripsikan dengan `picture_prompt`, atau `prompt` jika kosong.
    Objek yang dikembalikan hanya untuk diteruskan ke `convert`.
    """
    options = VlmPipelineOptions(enable_remote_services=True, images_scale=1.0)
    options.vlm_options = ApiVlmOptions(
        url=url,  # type: ignore
        params={
            "model": model,
            "max_tokens": max_tokens,
            "skip_special_tokens": skip_special_tokens,
        },
        headers=_auth_headers(api_key),
        prompt=prompt,
        timeout=timeout,
        scale=scale,
        temperature=temperature,
        response_format=find_response_format(response_format),
    )

    if enable_picture_description:
        options.do_picture_description = True
        options.generate_picture_images = True
        options.picture_description_options = PictureDescriptionApiOptions(
            url=url,  # type: ignore
            params={
                "model": model,
                "max_tokens": max_tokens,
                "skip_special_tokens": skip_special_tokens,
            },
            headers=_auth_headers(api_key),
            prompt=picture_prompt or prompt,
        )

    return DocumentConverter(
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.IMAGE,
            InputFormat.DOCX,
            InputFormat.HTML,
            InputFormat.PPTX,
            InputFormat.ASCIIDOC,
            InputFormat.CSV,
            InputFormat.MD,
        ],
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=options, pipeline_cls=VlmPipeline
            ),
            InputFormat.IMAGE: ImageFormatOption(
                pipeline_options=options, pipeline_cls=VlmPipeline
            ),
            InputFormat.DOCX: WordFormatOption(pipeline_options=options),
            InputFormat.HTML: HTMLFormatOption(pipeline_options=options),
            InputFormat.PPTX: PowerpointFormatOption(pipeline_options=options),
            InputFormat.ASCIIDOC: AsciiDocFormatOption(pipeline_options=options),
            InputFormat.CSV: CsvFormatOption(pipeline_options=options),
            InputFormat.MD: MarkdownFormatOption(pipeline_options=options),
        },
    )


# --------------------------------------------------------------------------
# Konversi Dan Ekspor
# --------------------------------------------------------------------------


def convert(converter: Any, path: str) -> Any:
    """Konversi satu dokumen dengan converter dari `create_converter`.

    Hasilnya ConversionResult milik Docling, apa adanya. Bacalah isinya
    dengan fungsi export_* di bawah, atau lewat `result.document`.
    """
    return converter.convert(path)


def export_markdown(result: Any) -> str:
    """Dokumen hasil `convert` sebagai Markdown."""
    return result.document.export_to_markdown()


def export_text(result: Any) -> str:
    """Dokumen hasil `convert` sebagai teks polos."""
    return result.document.export_to_text()


def export_dict(result: Any) -> dict:
    """Dokumen hasil `convert` sebagai dict, sesuai skema dokumen Docling."""
    return result.document.export_to_dict()

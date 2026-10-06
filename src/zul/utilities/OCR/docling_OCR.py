"""
Konversi dokumen ke Markdown / teks / dict dengan Docling dan Vision Language Model.

Gunanya:
    Membaca PDF, gambar, DOCX, PPTX, HTML, CSV, dan Markdown, lalu
    mengubahnya menjadi teks terstruktur. Halaman PDF dan gambar dikirim ke
    VLM lewat endpoint chat completions yang kompatibel dengan OpenAI.

Cara pakai:
    from zul.utilities.OCR.docling_OCR import DoclingVLMConverter

    converter = DoclingVLMConverter(
        model="Qwen3-VL-8B-Instruct",
        hostname_and_port="https://HOST/v1/chat/completions",
        api_key="API_KEY",
        prompt="Convert this page to markdown.",
        response_format="markdown",
    )

    markdown = converter.convert_to_markdown("dokumen.pdf")
    text = converter.convert_to_text("dokumen.pdf")

Menyertakan deskripsi gambar dan flowchart:
    converter = DoclingVLMConverter(..., enable_picture_description=True,
                                    picture_prompt="Describe the flowchart in detail.")

Mengambil tabel sebagai DataFrame:
    result = converter.convert("dokumen.pdf")
    for table in result.document.tables:
        dataframe = table.export_to_dataframe(doc=result.document)
"""

import os
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
# Nilai Bawaan
# --------------------------------------------------------------------------
#
# Model dan endpoint ini dipakai oleh create_default(). Keduanya
# bisa diganti lewat environment variable DOCLING_VLM_MODEL
# dan DOCLING_VLM_URL, tanpa menyentuh kode sama sekali.
#

DEFAULT_VLM_MODEL = "ops/Qwen3-VL-8B-Instruct"
DEFAULT_VLM_URL = "https://llmservice.air.id/chat/completions"

# --------------------------------------------------------------------------
# Format Respons
# --------------------------------------------------------------------------
#
# Kunci selalu ditulis dengan huruf kecil sebab response_format dari
# pemanggil diubah ke huruf kecil lebih dulu sebelum dicocokkan.
# Dengan begitu "Markdown" dan "markdown" sama-sama diterima.
#

RESPONSE_FORMATS = {
    "doctags": ResponseFormat.DOCTAGS,
    "markdown": ResponseFormat.MARKDOWN,
    "deepseek_markdown": ResponseFormat.DEEPSEEKOCR_MARKDOWN,
    "html": ResponseFormat.HTML,
    "otsl": ResponseFormat.OTSL,
    "plaintext": ResponseFormat.PLAINTEXT,
}

# --------------------------------------------------------------------------
# Konverter Dokumen
# --------------------------------------------------------------------------


class DoclingVLMConverter:
    """
    Utility class for configuring and creating DocumentConverter instances
    with VLM (Vision Language Model) pipeline support.
    """

    def __init__(
        self,
        model: str,
        hostname_and_port: str,
        api_key: str = "",
        prompt: str = "Convert this page to docling.",
        picture_prompt: str | None = None,
        response_format: str = "doctags",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        skip_special_tokens: bool = False,
        timeout: int = 90,
        scale: float = 2.0,
        enable_picture_description: bool = False,
    ):
        """
        Initialize the DoclingVLMConverter.

        Args:
            model: Nama model VLM di endpoint.
            hostname_and_port: URL lengkap endpoint chat completions
                (OpenAI-compatible).
            api_key: API key; kosong berarti tanpa header Authorization.
            prompt: Prompt konversi per halaman.
            picture_prompt: Prompt deskripsi gambar; default = prompt +
                instruksi diagram.
            response_format: doctags | markdown | deepseek_markdown | html |
                otsl | plaintext (tidak case-sensitive).
            enable_picture_description: Deskripsikan gambar/flowchart dengan VLM.
        """
        format_key = response_format.lower()
        if format_key not in RESPONSE_FORMATS:
            valid_formats = ", ".join(RESPONSE_FORMATS)
            raise ValueError(
                f"Invalid response_format '{response_format}'. "
                f"Valid options: {valid_formats}"
            )

        self.model = model
        self.hostname_and_port = hostname_and_port
        self.api_key = api_key
        self.prompt = prompt
        self.picture_prompt = (
            picture_prompt
            or prompt + " Describe diagrams, flowcharts, and shapes concisely."
        )
        self.response_format = RESPONSE_FORMATS[format_key]
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.skip_special_tokens = skip_special_tokens
        self.timeout = timeout
        self.scale = scale
        self.enable_picture_description = enable_picture_description

        self._doc_converter = None

    # ----------------------------------------------------------------------
    # Opsi Pipeline VLM
    # ----------------------------------------------------------------------

    def _create_vlm_options(self) -> ApiVlmOptions:
        """Create VLM options for OpenAI-compatible endpoints."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return ApiVlmOptions(
            url=self.hostname_and_port,  # type: ignore
            params={
                "model": self.model,
                "max_tokens": self.max_tokens,
                "skip_special_tokens": self.skip_special_tokens,
            },
            headers=headers,
            prompt=self.prompt,
            timeout=self.timeout,
            scale=self.scale,
            temperature=self.temperature,
            response_format=self.response_format,
        )

    def _create_pipeline_options(self) -> VlmPipelineOptions:
        """Create VLM pipeline options with remote services enabled."""
        pipeline_options = VlmPipelineOptions(
            enable_remote_services=True,
            images_scale=1.0,
        )
        pipeline_options.vlm_options = self._create_vlm_options()

        if self.enable_picture_description:
            pipeline_options.do_picture_description = True
            pipeline_options.generate_picture_images = True
            pipeline_options.picture_description_options = PictureDescriptionApiOptions(
                url=self.hostname_and_port,  # type: ignore
                params={
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "skip_special_tokens": self.skip_special_tokens,
                },
                headers=(
                    {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                ),
                prompt=self.picture_prompt,
            )

        return pipeline_options

    def _get_converter(self) -> DocumentConverter:
        """Get or create the underlying DocumentConverter instance."""
        if self._doc_converter is None:
            pipeline_options = self._create_pipeline_options()

            self._doc_converter = DocumentConverter(
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
                        pipeline_options=pipeline_options, pipeline_cls=VlmPipeline
                    ),
                    InputFormat.IMAGE: ImageFormatOption(
                        pipeline_options=pipeline_options, pipeline_cls=VlmPipeline
                    ),
                    InputFormat.DOCX: WordFormatOption(
                        pipeline_options=pipeline_options
                    ),
                    InputFormat.HTML: HTMLFormatOption(
                        pipeline_options=pipeline_options
                    ),
                    InputFormat.PPTX: PowerpointFormatOption(
                        pipeline_options=pipeline_options
                    ),
                    InputFormat.ASCIIDOC: AsciiDocFormatOption(
                        pipeline_options=pipeline_options
                    ),
                    InputFormat.CSV: CsvFormatOption(pipeline_options=pipeline_options),
                    InputFormat.MD: MarkdownFormatOption(
                        pipeline_options=pipeline_options
                    ),
                },
            )
        return self._doc_converter

    # ----------------------------------------------------------------------
    # Konversi Dokumen
    # ----------------------------------------------------------------------

    def convert(self, document_path: str) -> Any:
        """
        Convert a document using converter.convert() and return the RAW result object.

        Access exports via:
        - result.document.export_to_dict()
        - result.document.export_to_markdown()
        - result.document.export_to_text()

        Args:
            document_path: Path to the document to convert

        Returns:
            Raw ConversionResult from DocumentConverter.convert()
        """
        converter = self._get_converter()
        return converter.convert(document_path)  # Returns raw result

    def convert_to_dict(self, document_path: str) -> dict:
        """Convert and return result.document.export_to_dict()."""
        result = self.convert(document_path)
        return result.document.export_to_dict()

    def convert_to_text(self, document_path: str) -> str:
        """Convert and return result.document.export_to_text()."""
        result = self.convert(document_path)
        return result.document.export_to_text()

    def convert_to_markdown(self, document_path: str) -> str:
        """Convert and return result.document.export_to_markdown()."""
        result = self.convert(document_path)
        return result.document.export_to_markdown()

    # ----------------------------------------------------------------------
    # Konstruktor Alternatif
    # ----------------------------------------------------------------------

    @classmethod
    def create_default(
        cls, api_key: str = "sk", enable_picture_description: bool = False
    ) -> "DoclingVLMConverter":
        """
        Create default converter for Qwen3-VL-8B-Instruct.

        Model dan endpoint bisa diganti lewat environment variable
        DOCLING_VLM_MODEL dan DOCLING_VLM_URL.
        """
        return cls(
            model=os.getenv("DOCLING_VLM_MODEL", DEFAULT_VLM_MODEL),
            hostname_and_port=os.getenv("DOCLING_VLM_URL", DEFAULT_VLM_URL),
            api_key=api_key,
            prompt="Convert this page to markdown.",
            response_format="markdown",
            enable_picture_description=enable_picture_description,
        )


# --------------------------------------------------------------------------
# Contoh Pemakaian
# --------------------------------------------------------------------------

if __name__ == "__main__":
    # Method 1: Using default configuration and getting result object
    converter = DoclingVLMConverter.create_default(api_key="sk")
    result = converter.convert("document.pdf")

    # Now you can use the framework's built-in export methods
    dict_output = result.document.export_to_dict()
    text_output = result.document.export_to_text()
    markdown_output = result.document.export_to_markdown()

    # Method 2: Direct convenience methods (does the same thing in one step)
    converter = DoclingVLMConverter.create_default(api_key="sk")

    markdown = converter.convert_to_markdown("document.pdf")
    text = converter.convert_to_text("document.pdf")
    data = converter.convert_to_dict("document.pdf")

    # Method 3: Custom configuration
    custom_converter = DoclingVLMConverter(
        model="icon/Qwen3-VL-8B-Instruct",
        hostname_and_port="https://llmservice.air.id/chat/completions",
        api_key="your-api-key",
        prompt="Extract all text from this document.",
        temperature=0.5,
        max_tokens=8192,
    )

    result = custom_converter.convert("document.pdf")
    markdown = result.document.export_to_markdown()

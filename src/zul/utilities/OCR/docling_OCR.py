from typing import Dict, Any
from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions, ResponseFormat
from docling.datamodel.pipeline_options import (
    VlmPipelineOptions,
    PictureDescriptionApiOptions,
)
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    ImageFormatOption,
    WordFormatOption,
    HTMLFormatOption,
    PowerpointFormatOption,
    AsciiDocFormatOption,
    CsvFormatOption,
    MarkdownFormatOption,
)
from docling.datamodel.base_models import InputFormat
from docling.pipeline.vlm_pipeline import VlmPipeline
from typing import Any, Dict
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    VlmPipelineOptions,
    PictureDescriptionApiOptions,
)
from docling.pipeline.vlm_pipeline import VlmPipeline


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
        picture_prompt: str = None,  # type: ignore
        response_format: str = "doctags",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        skip_special_tokens: bool = False,
        timeout: int = 90,
        scale: float = 2.0,
        enable_picture_description: bool = False,
    ):
        """
        Initialize the DoclingVLMConverter. See previous docstring.
        """
        format_mapping = {
            "doctags": ResponseFormat.DOCTAGS,
            "markdown": ResponseFormat.MARKDOWN,
            "deepseek_markdown": ResponseFormat.DEEPSEEKOCR_MARKDOWN,
            "HTML": ResponseFormat.HTML,
            "otsl": ResponseFormat.OTSL,
            "plaintext": ResponseFormat.PLAINTEXT,
        }

        format_key = response_format.lower()
        if format_key not in format_mapping:
            valid_formats = ", ".join(format_mapping.keys())
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
        self.response_format = format_mapping[format_key]
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.skip_special_tokens = skip_special_tokens
        self.timeout = timeout
        self.scale = scale
        self.enable_picture_description = enable_picture_description

        self._doc_converter = None

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
                # temperature=self.temperature, # type: ignore
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

    def convert_to_dict(self, document_path: str) -> Dict:
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

    @classmethod
    def create_default(
        cls, api_key: str = "sk", enable_picture_description: bool = False
    ) -> "DoclingVLMConverter":
        """Create default converter for Qwen3-VL-8B-Instruct."""
        return cls(
            model="ops/Qwen3-VL-8B-Instruct",
            hostname_and_port="https://llmservice.air.id/chat/completions",
            api_key=api_key,
            prompt="Convert this page to markdown.",
            response_format="markdown",
            enable_picture_description=enable_picture_description,
        )


# Example usage:
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

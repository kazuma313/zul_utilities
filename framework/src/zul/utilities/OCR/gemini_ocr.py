"""
OCR dokumen PDF dengan Google Gemini (butuh `pip install "zul[gemini]"`).

Gunanya:
    Mengunggah PDF ke Gemini, meminta model mengekstrak isinya sesuai
    prompt, lalu menghapus file dari server Gemini setelah selesai. Semua
    pemanggilan SDK google-genai lewat zul.adapters.gemini.

Cara pakai:
    import os
    from zul.utilities.OCR.gemini_ocr import (
        create_gemini_client, process_pdf_with_gemini, setup_logger,
    )

    logger = setup_logger()
    client = create_gemini_client(api_key=os.environ["GOOGLE_API_KEY"], logger=logger)

    markdown = process_pdf_with_gemini(
        client=client,
        pdf_path="dokumen.pdf",
        prompt="Extract the text content from this PDF as markdown.",
        logger=logger,
        model_name="gemini-2.5-pro",
    )

Kedua fungsi mengembalikan None jika gagal (API key kosong, file tidak
ada, atau request error); detailnya ditulis ke logger. Client dari
`create_gemini_client` adalah genai.Client milik google-genai, dibuat
oleh zul.adapters.gemini.
"""

import logging
import os
from typing import Any

from zul.adapters import gemini as gemini_adapter

# --------------------------------------------------------------------------
# Logger dan Client
# --------------------------------------------------------------------------


def setup_logger():
    """Sets up a basic console logger."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


def create_gemini_client(api_key: str, logger: logging.Logger) -> Any | None:
    """
    Initializes and returns a Gemini client.

    Args:
        api_key (str): Your Google API key.
        logger (logging.Logger): The logger instance.

    Returns:
        genai.Client | None: An initialized client object, or None if creation fails.
    """
    if not api_key:
        logger.critical("Google API key is missing. Cannot create client.")
        return None
    try:
        logger.info("Initializing Gemini client...")
        client = gemini_adapter.create_client(api_key)
        logger.info("Gemini client initialized successfully.")
        return client
    except Exception:
        logger.error("Failed to initialize Gemini client.", exc_info=True)
        return None


# --------------------------------------------------------------------------
# Memproses PDF
# --------------------------------------------------------------------------
#
# File diunggah dulu ke server Gemini, baru dirujuk dalam request bersama
# prompt. Blok finally menghapus file itu dari server baik request-nya
# berhasil maupun gagal, supaya dokumen tidak tertinggal di server.
#


def process_pdf_with_gemini(
    client: Any,
    pdf_path: str,
    prompt: str,
    logger: logging.Logger,
    model_name: str = "gemini-2.5-pro",
) -> str | None:
    """
    Uses a pre-initialized Gemini client to process a PDF.

    Args:
        client (genai.Client): An active and initialized Gemini client instance.
        pdf_path (str): The local file path to the PDF.
        prompt (str): The prompt to send to the model.
        logger (logging.Logger): The logger instance for output.
        model_name (str, optional): The Gemini model to use.
            Defaults to "gemini-2.5-pro".

    Returns:
        str | None: The generated text content, or None if an error occurs.
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at path: {pdf_path}")
        return None

    uploaded_file = None
    try:
        file_basename = os.path.basename(pdf_path)
        logger.info(f"Uploading file: '{file_basename}'...")
        uploaded_file = gemini_adapter.upload_file(client, pdf_path)
        logger.info(f"File uploaded successfully. URI: {uploaded_file.uri}")

        logger.info(f"Sending request to Gemini model '{model_name}'...")
        text = gemini_adapter.generate_text(
            client, model=model_name, prompt=prompt, file=uploaded_file
        )
        logger.info("Response received successfully.")
        return text

    except Exception:
        logger.error(
            "An error occurred during the PDF processing workflow.", exc_info=True
        )
        return None

    finally:
        if uploaded_file:
            logger.info(f"Deleting uploaded file from server: {uploaded_file.name}...")
            try:
                gemini_adapter.delete_file(client, uploaded_file.name)
                logger.info("File cleanup complete.")
            except Exception:
                logger.error(
                    f"Failed to delete file {uploaded_file.name}.", exc_info=True
                )


# --------------------------------------------------------------------------
# Contoh Pemakaian
# --------------------------------------------------------------------------

if __name__ == "__main__":
    logger = setup_logger()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    client = create_gemini_client(api_key=GOOGLE_API_KEY, logger=logger)

    OCR_PROMPT = (
        "Extract the text content from this PDF and return it in markdown format."
    )
    pdf_path_1 = "path/to/your/document.pdf"
    response = process_pdf_with_gemini(
        client=client,
        pdf_path=pdf_path_1,
        prompt=OCR_PROMPT,
        model_name="gemini-2.5-pro",
        logger=logger,
    )

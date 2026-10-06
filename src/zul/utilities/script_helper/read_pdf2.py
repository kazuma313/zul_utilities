"""
Baca PDF dan potong isinya menjadi chunk.

Gunanya:
    Langkah awal pipeline RAG untuk PDF yang teksnya bisa diekstrak langsung
    (bukan hasil scan; untuk scan pakai `zul.utilities.OCR`).

Cara pakai (`pip install "zul[pdf]"`):
    from zul.utilities.script_helper.read_pdf2 import PDFProcessor

    pdf = PDFProcessor()

    pages = pdf.read_pdf_pages("dokumen.pdf")            # list teks per halaman
    text = pdf.read_pdf_as_single_text("dokumen.pdf")    # satu string

    chunks = pdf.chunk_recursive_character_splitter(
        "dokumen.pdf", chunk_size=1000, overlap=200,
    )                                                    # list Document LangChain
    per_page = pdf.chunk_per_page("dokumen.pdf")         # satu Document per halaman

    stats = pdf.process_folder("folder_pdf/")            # ringkasan semua PDF

Contoh:
    pdf_processor = PDFProcessor()

    pdf_files = pdf_processor.get_pdf_files("/path/to/pdf/folder")
    print(f"Found {len(pdf_files)} PDF files")

    pages = pdf_processor.read_pdf_pages("document.pdf")
    if pages:
        print(f"PDF has {len(pages)} pages")

        full_text = pdf_processor.list_to_text(pages)
        print(f"Total text length: {len(full_text)}")

        min_len, max_len = pdf_processor.get_min_max_length_list(pages)
        print(f"Page lengths: min={min_len}, max={max_len}")

Method tidak melempar exception saat PDF gagal dibaca; mereka mengembalikan
None atau list kosong dan menyimpan pesannya di `pdf.last_error`.
"""

import os

try:
    from pypdf import PdfReader
except ImportError:  # PyPDF2 adalah nama lama pypdf
    from PyPDF2 import PdfReader
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --------------------------------------------------------------------------
# Konfigurasi
# --------------------------------------------------------------------------


@dataclass
class PDFConfig:
    """Configuration for PDF operations"""

    encoding: str = "utf-8"
    strict: bool = False  # pypdf strict mode
    verbose: bool = True  # Print error messages


# --------------------------------------------------------------------------
# Pemroses PDF
# --------------------------------------------------------------------------
#
# Setiap method menangkap error-nya sendiri lalu menyimpannya di last_error.
# Jadi satu PDF yang rusak tidak membatalkan pemrosesan semua isi folder.
#


class PDFProcessor:
    """
    A comprehensive PDF processing class that handles:
    - Finding PDF files in directories
    - Reading PDF content
    - Text manipulation and analysis
    """

    def __init__(self, config: PDFConfig | None = None):
        self.config = config or PDFConfig()
        self._pdf_files: list[str] = []
        self._last_error: str | None = None

    # ----------------------------------------------------------------------
    # Mencari dan Membaca PDF
    # ----------------------------------------------------------------------

    def get_pdf_files(self, folder_path: str | Path) -> list[str]:
        """
        Get all PDF files from a folder recursively

        Args:
            folder_path: Path to the folder to scan

        Returns:
            List of PDF file paths
        """
        pdf_files = []
        folder_path = Path(folder_path)

        try:
            # Check if folder exists
            if not folder_path.exists():
                self._handle_error(f"Folder does not exist: {folder_path}")
                return []

            # Walk through the directory recursively
            for root, _dirs, files in os.walk(folder_path):
                pdf_files.extend(
                    [
                        os.path.join(root, file)
                        for file in files
                        if file.lower().endswith(".pdf")
                    ]
                )

            self._pdf_files = pdf_files
            return pdf_files

        except Exception as e:
            self._handle_error(f"Error scanning folder: {str(e)}")
            return []

    def read_pdf_pages(self, file_path: str | Path) -> list[str] | None:
        """
        Read a PDF file and return text content of each page

        Args:
            file_path: Path to the PDF file

        Returns:
            List of text content for each page, or None if error
        """
        file_path = Path(file_path)

        try:
            # Check if file exists
            if not file_path.exists():
                self._handle_error(f"PDF file does not exist: {file_path}")
                return None

            with open(file_path, "rb") as file:
                pdf_reader = PdfReader(file, strict=self.config.strict)

                # Extract text from each page
                pages_text = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        pages_text.append(text.strip() if text else "")
                    except Exception as page_error:
                        self._handle_error(
                            f"Error reading page {page_num + 1}: {str(page_error)}"
                        )
                        pages_text.append("")

                return pages_text

        except Exception as e:
            self._handle_error(f"Error reading PDF {file_path}: {str(e)}")
            return None

    def read_pdf_as_single_text(self, file_path: str | Path) -> str | None:
        """
        Read PDF and return as single concatenated text

        Args:
            file_path: Path to the PDF file

        Returns:
            Single text string or None if error
        """
        pages = self.read_pdf_pages(file_path)
        if pages is None:
            return None

        return self.list_to_text(pages)

    # ----------------------------------------------------------------------
    # Memotong Menjadi Chunk
    # ----------------------------------------------------------------------

    def chunk_per_page(
        self,
        file_path: str | Path,
    ):
        """
        Satu Document LangChain untuk tiap halaman PDF.

        Args:
            file_path: Path ke file PDF.

        Returns:
            List Document; kosong jika PDF gagal dibaca.
        """
        pages = self.read_pdf_pages(file_path)
        if pages is None:
            return []
        return [Document(page) for page in pages]

    def chunk_recursive_character_splitter(
        self,
        file_path: str | Path,
        chunk_size: int = 4000,
        overlap: int = 450,
        separators: list[str] | None = None,
        length_function: Callable[[str], int] | None = len,
        is_sperator: bool = True,
    ):
        """
        Baca PDF lalu potong teksnya dengan RecursiveCharacterTextSplitter.

        Args:
            file_path: Path ke file PDF.
            chunk_size: Panjang tiap chunk dalam karakter. Bawaan 4000.
            overlap: Jumlah karakter yang tumpang tindih. Bawaan 450.
            separators: Daftar pemisah chunk, dicoba berurutan. Bawaan
                paragraf, baris, spasi, lalu karakter.
            length_function: Fungsi pengukur panjang teks. Bawaan len.
            is_sperator: True jika separators berupa regex. Bawaan True.

        Returns:
            List Document LangChain; kosong jika PDF gagal dibaca.
        """
        if separators is None:
            separators = ["\n\n", "\n", " ", ""]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=length_function,
            is_separator_regex=is_sperator,
            separators=separators,
        )

        text = self.read_pdf_as_single_text(file_path)
        recursive_chunk = text_splitter.create_documents([text]) if text else []

        return recursive_chunk

    # ----------------------------------------------------------------------
    # Pembantu Teks
    # ----------------------------------------------------------------------

    @staticmethod
    def list_to_text(list_of_text: list[str]) -> str:
        """
        Convert list of text to single text

        Args:
            list_of_text: List of text strings

        Returns:
            Single concatenated text string
        """
        if not list_of_text:
            return ""

        return "\n".join(list_of_text).strip()

    @staticmethod
    def get_min_max_length_list(document: list[str | object]) -> tuple[int, int]:
        """
        Get minimum and maximum length from a list of strings or chunks

        Args:
            document: List of text strings or objects with page_content attribute

        Returns:
            Tuple containing (minimum length, maximum length)
        """
        if not document:
            return (0, 0)

        # Handle both string lists and objects with page_content
        lengths = []
        for item in document:
            if hasattr(item, "page_content"):
                lengths.append(len(item.page_content))
            elif isinstance(item, str):
                lengths.append(len(item))
            else:
                lengths.append(len(str(item)))

        return (min(lengths), max(lengths)) if lengths else (0, 0)

    # ----------------------------------------------------------------------
    # Memproses Satu Folder
    # ----------------------------------------------------------------------

    def process_folder(self, folder_path: str | Path) -> dict:
        """
        Process entire folder and return comprehensive stats

        Args:
            folder_path: Path to folder containing PDFs

        Returns:
            Dictionary with processing results and statistics
        """
        pdf_files = self.get_pdf_files(folder_path)

        results = {
            "total_files": len(pdf_files),
            "processed_files": 0,
            "failed_files": 0,
            "total_pages": 0,
            "files_data": [],
        }

        for pdf_file in pdf_files:
            pages = self.read_pdf_pages(pdf_file)

            if pages is not None:
                file_data = {
                    "file_path": pdf_file,
                    "pages_count": len(pages),
                    "total_text_length": len(self.list_to_text(pages)),
                    "min_max_page_length": self.get_min_max_length_list(pages),
                }

                results["files_data"].append(file_data)
                results["processed_files"] += 1
                results["total_pages"] += len(pages)
            else:
                results["failed_files"] += 1

        return results

    # ----------------------------------------------------------------------
    # Error dan Status
    # ----------------------------------------------------------------------

    def _handle_error(self, error_message: str) -> None:
        """Internal method to handle errors consistently"""
        self._last_error = error_message
        if self.config.verbose:
            print(f"PDFProcessor Error: {error_message}")

    @property
    def last_error(self) -> str | None:
        """Get the last error that occurred"""
        return self._last_error

    @property
    def found_pdf_files(self) -> list[str]:
        """Get list of PDF files found in last scan"""
        return self._pdf_files.copy()

    def __len__(self) -> int:
        """Return number of PDF files found"""
        return len(self._pdf_files)

    def __repr__(self) -> str:
        return (
            f"PDFProcessor(files_found={len(self._pdf_files)}, "
            f"last_error={self._last_error})"
        )

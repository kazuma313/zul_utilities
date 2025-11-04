import os
import markdown
from io import BytesIO
from xhtml2pdf import pisa
from typing import Optional


class MarkdownToPDFConverter:
    """
    Class untuk mengkonversi Markdown menjadi PDF dengan styling yang rapi.

    Attributes:
        page_size (str): Ukuran halaman PDF (default: "A4")
        margin (str): Margin halaman (default: "2cm")
        markdown_extensions (list): Extensions untuk markdown parser

    Example:
        >>> converter = MarkdownToPDFConverter()
        >>> converter.convert("# Hello World", "/path/to/output", "hello.pdf")
    """

    DEFAULT_STYLES = """
    @page {{
        size: {page_size};
        margin: {margin};
    }}
    * {{
        box-sizing: border-box;
    }}
    body {{
        font-family: 'Arial', sans-serif;
        font-size: 10pt;
        line-height: 1.5;
        color: #000;
    }}
    h1 {{
        color: #000;
        text-align: left;
        font-size: 16pt;
        font-weight: bold;
        margin: 25px 0 15px 0;
        padding: 10px 0 10px 15px;
        border-left: 5px solid #FFA500;
        background-color: #FFF8E7;
        page-break-after: avoid;
    }}
    h2 {{
        color: #000;
        text-align: left;
        font-size: 14pt;
        font-weight: bold;
        margin: 20px 0 15px 0;
        padding: 8px 0 8px 12px;
        border-left: 4px solid #FFB84D;
        background-color: #FFFAF0;
        page-break-after: avoid;
    }}
    h3 {{
        color: #000;
        text-align: left;
        font-size: 13pt;
        font-weight: bold;
        margin: 18px 0 12px 0;
        padding: 8px 0 8px 12px;
        border-left: 4px solid #FFB84D;
        background-color: #FFFAF0;
        page-break-after: avoid;
    }}
    h4 {{
        color: #000;
        text-align: left;
        font-size: 12pt;
        font-weight: bold;
        margin: 15px 0 10px 0;
        padding: 6px 0 6px 10px;
        border-left: 3px solid #FFC166;
        page-break-after: avoid;
    }}
    h5 {{
        color: #000;
        text-align: left;
        font-size: 11pt;
        font-weight: bold;
        margin: 12px 0 8px 0;
        padding: 5px 0 5px 8px;
        border-left: 2px solid #FFD699;
        page-break-after: avoid;
    }}
    p {{
        text-align: justify;
        margin: 8px 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}
    ul, ol {{
        margin: 8px 0;
        padding-left: 25px;
    }}
    li {{
        text-align: justify;
        margin: 4px 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 12px 0;
        font-size: 9pt;
        table-layout: fixed;
        page-break-inside: auto;
    }}
    table th {{
        border: 1px solid #000;
        padding: 8px 6px;
        text-align: center;
        background-color: #FFA500;
        color: #000;
        font-weight: bold;
        vertical-align: middle;
        word-wrap: break-word;
        hyphens: auto;
    }}
    table td {{
        border: 1px solid #000;
        padding: 6px 5px;
        text-align: justify;
        vertical-align: top;
        background-color: #FFF;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.4;
    }}
    table tr {{
        page-break-inside: avoid;
    }}
    /* Tabel 2 kolom (Informasi Program, Deskripsi, dll) */
    table.two-column td:first-child {{
        width: 25%;
        font-weight: bold;
        text-align: left;
    }}
    table.two-column td:nth-child(2) {{
        width: 75%;
    }}
    /* Tabel 3 kolom (Evaluasi, Rekomendasi) */
    table.three-column td:first-child {{
        width: 10%;
        text-align: center;
        font-weight: bold;
    }}
    table.three-column td:nth-child(2) {{
        width: 90%;
    }}
    /* Tabel silabus (6 kolom) */
    table.silabus td:first-child {{
        width: 5%;
        text-align: center;
        font-weight: bold;
    }}
    table.silabus td:nth-child(2) {{
        width: 20%;
    }}
    table.silabus td:nth-child(3) {{
        width: 10%;
        text-align: center;
    }}
    table.silabus td:nth-child(4) {{
        width: 20%;
    }}
    table.silabus td:nth-child(5) {{
        width: 20%;
    }}
    table.silabus td:nth-child(6) {{
        width: 25%;
    }}
    strong {{
        font-weight: bold;
    }}
    br {{
        line-height: 1.8;
    }}
    code {{
        background-color: #f4f4f4;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 9pt;
        word-wrap: break-word;
    }}
    pre {{
        background-color: #f4f4f4;
        padding: 10px;
        border-radius: 5px;
        overflow-x: auto;
        word-wrap: break-word;
        white-space: pre-wrap;
        font-size: 9pt;
    }}
    """

    def __init__(
        self,
        page_size: str = "A4",
        margin: str = "2cm",
        markdown_extensions: Optional[list] = None,
    ):
        """
        Inisialisasi converter dengan konfigurasi.

        Args:
            page_size (str): Ukuran halaman PDF
            margin (str): Margin halaman
            markdown_extensions (list): Extensions untuk markdown parser
        """
        self.page_size = page_size
        self.margin = margin
        self.markdown_extensions = markdown_extensions or [
            "extra",
            "codehilite",
            "tables",
        ]

    def get_styles(self) -> str:
        """Menghasilkan CSS styling untuk PDF."""
        return self.DEFAULT_STYLES.format(page_size=self.page_size, margin=self.margin)

    def create_html_document(self, content: str) -> str:
        """
        Membuat dokumen HTML lengkap dari konten.

        Args:
            content (str): HTML content

        Returns:
            str: Dokumen HTML lengkap
        """
        styles = self.get_styles()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>{styles}</style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """

    def markdown_to_html(self, markdown_content: str) -> str:
        """
        Konversi Markdown ke HTML.

        Args:
            markdown_content (str): Konten Markdown

        Returns:
            str: Konten HTML
        """
        return markdown.markdown(markdown_content, extensions=self.markdown_extensions)

    def convert(
        self, markdown_content: str, output_path: str, filename: str = "output.pdf"
    ) -> bool:
        """
        Konversi Markdown menjadi PDF.

        Args:
            markdown_content (str): Konten dalam format Markdown
            output_path (str): Path direktori tempat menyimpan PDF
            filename (str): Nama file PDF

        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            # Convert Markdown to HTML
            html_content = self.markdown_to_html(markdown_content)

            # Buat HTML document lengkap
            html_document = self.create_html_document(html_content)

            # Pastikan direktori output ada
            os.makedirs(output_path, exist_ok=True)

            # Path lengkap file output
            output_file = os.path.join(output_path, filename)

            # Simpan ke PDF
            with open(output_file, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(html_document, dest=pdf_file)

            if pisa_status.err:  # type: ignore
                print("✗ Error saat membuat PDF")
                return False

            print(f"✓ PDF berhasil disimpan di: {output_file}")
            print(f"✓ Absolute path: {os.path.abspath(output_file)}")
            return True

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def convert_to_bytes(self, markdown_content: str) -> bytes:
        """
        Konversi Markdown menjadi PDF dalam bentuk bytes (in-memory).

        Args:
            markdown_content (str): Konten dalam format Markdown.

        Returns:
            bytes: File PDF dalam bentuk bytes.
        """
        try:
            # Convert Markdown ke HTML
            html_content = self.markdown_to_html(markdown_content)

            # Buat dokumen HTML lengkap
            html_document = self.create_html_document(html_content)

            # Simpan PDF ke memori (bukan file fisik)
            pdf_io = BytesIO()
            pisa_status = pisa.CreatePDF(html_document, dest=pdf_io)
            pdf_io.seek(0)

            if pisa_status.err:  # type: ignore
                raise Exception("Gagal membuat PDF dari Markdown.")

            return pdf_io.getvalue()

        except Exception as e:
            print(f"✗ Error saat konversi ke bytes: {e}")
            return b""

    def convert_from_response(
        self, response, output_path: str, filename: str = "output.pdf"
    ) -> bool:
        """
        Konversi response JSON (dari API) yang berisi Markdown menjadi PDF.

        Args:
            response: Response object yang memiliki method .json()
            output_path (str): Path direktori tempat menyimpan PDF
            filename (str): Nama file PDF

        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            markdown_content = response.json()
            return self.convert(markdown_content, output_path, filename)
        except Exception as e:
            print(f"✗ Error saat memproses response: {e}")
            return False

    def set_custom_styles(self, custom_styles: str) -> None:
        """
        Set custom CSS styles untuk PDF.

        Args:
            custom_styles (str): Custom CSS string
        """
        self.DEFAULT_STYLES = custom_styles


# Contoh penggunaan
if __name__ == "__main__":
    # Contoh 1: Penggunaan dasar
    converter = MarkdownToPDFConverter()

    sample_markdown = """
# Judul Dokumen

## Sub Judul

Ini adalah **paragraf** dengan *italic* dan `code inline`.

### Daftar
- Item 1
- Item 2
- Item 3

### Tabel
| Kolom 1 | Kolom 2 |
|---------|---------|
| Data 1  | Data 2  |
| Data 3  | Data 4  |

```python
def hello():
    print("Hello World")
```
    """

    converter.convert(
        markdown_content=sample_markdown,
        output_path="/Users/rizalmaulana/Downloads",
        filename="contoh_dokumen.pdf",
    )

    # Contoh 2: Dengan konfigurasi custom
    custom_converter = MarkdownToPDFConverter(page_size="Letter", margin="1.5cm")

    custom_converter.convert(
        markdown_content=sample_markdown,
        output_path="/Users/rizalmaulana/Downloads",
        filename="custom_dokumen.pdf",
    )

    # Contoh 3: Dari response API (uncomment jika ada response object)
    # converter.convert_from_response(
    #     response=response,
    #     output_path="/Users/rizalmaulana/Downloads",
    #     filename="content_contoh_persyaratan.pdf"
    # )


# DEFAULT_STYLES = """
#         @page {{
#             size: {page_size};
#             margin: {margin};
#         }}
#         body {{
#             font-family: 'Arial', sans-serif;
#             font-size: 12pt;
#             line-height: 1.6;
#             color: #333;
#         }}
#         h1 {{
#             color: #2c3e50;
#             border-bottom: 3px solid #3498db;
#             padding-bottom: 10px;
#             margin-top: 20px;
#         }}
#         h2 {{
#             color: #34495e;
#             border-bottom: 2px solid #95a5a6;
#             padding-bottom: 8px;
#             margin-top: 18px;
#         }}
#         h3 {{
#             color: #7f8c8d;
#             margin-top: 15px;
#         }}
#         p {{
#             text-align: justify;
#             margin: 10px 0;
#         }}
#         ul, ol {{
#             margin: 10px 0;
#             padding-left: 30px;
#         }}
#         code {{
#             background-color: #f4f4f4;
#             padding: 2px 6px;
#             border-radius: 3px;
#             font-family: 'Courier New', monospace;
#         }}
#         pre {{
#             background-color: #f4f4f4;
#             padding: 15px;
#             border-radius: 5px;
#             overflow-x: auto;
#         }}
#         table {{
#             border-collapse: collapse;
#             width: 100%;
#             margin: 15px 0;
#         }}
#         table th, table td {{
#             border: 1px solid #ddd;
#             padding: 8px;
#             text-align: left;
#         }}
#         table th {{
#             background-color: #3498db;
#             color: white;
#         }}
#     """

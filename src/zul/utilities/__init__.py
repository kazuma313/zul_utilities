"""
Utilities package: helper siap pakai untuk aplikasi AI.

Peta modul, dengan extra yang dibutuhkan di dalam kurung siku:
    vector_DB/            MilvusHelper [milvus], RedisHelper dan RedisVectorDB [redis]
    OCR/                  DoclingVLMConverter [ocr], OCR dengan Gemini [gemini]
    markdown_converter/   Markdown -> PDF dan Markdown -> PPTX [converter]
    embedding_service     AIService: chat + embedding dari satu config [llm]
    react_graph           graph LangGraph paling kecil [llm]
    fake_embedding        embedding palsu yang deterministik (untuk test)
    analysis              ChartGenerator: chart perbandingan + uji statistik [analysis]
    logger                logger console + file
    script_helper/        PDFProcessor [pdf], simpan file [analysis], AIService
                          ringkas [llm], timer, konversi JSON

Modul tanpa kurung siku sudah jalan dengan instalasi dasar. Extra dipasang
sesuai fitur yang dipakai, contoh:
    pip install "zul[milvus,redis]"
"""

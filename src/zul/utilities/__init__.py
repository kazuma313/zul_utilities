"""
Utilities package: helper siap pakai untuk aplikasi AI.

Peta modul:
    vector_DB/            MilvusHelper, RedisHelper, RedisVectorDB
    OCR/                  DoclingVLMConverter, OCR dengan Gemini
    markdown_converter/   Markdown -> PDF dan Markdown -> PPTX
    embedding_service     AIService: chat + embedding dari satu config
    fake_embedding        embedding palsu yang deterministik (untuk test)
    analysis              ChartGenerator: chart perbandingan + uji statistik
    logger                logger console + file
    script_helper/        PDFProcessor, timer, simpan file, konversi JSON

Dependency tiap modul dipasang lewat extra, contoh:
    pip install "zul[milvus,redis]"
"""

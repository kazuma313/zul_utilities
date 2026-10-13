"""
Tool: fungsi yang bisa dipanggil agent untuk mendapat fakta atau melakukan aksi.

Tool yang tersedia:
    weather_tool.py   get_weather  (contoh tool baca data)
    email_tool.py     send_email   (contoh tool dengan efek ke dunia luar)

Cara membuat tool baru:
    1. Buat file `nama_tool.py` dengan fungsi berdekorator `@tool`.
    2. Tulis docstring yang jelas: LLM membaca docstring dan nama argumen
       untuk memutuskan kapan dan bagaimana memanggil tool.
    3. Daftarkan di controller agent yang memakainya.

Contoh:
    from langchain.tools import tool

    @tool
    def get_order_status(order_id: str) -> str:
        '''Get the current status of an order.

        Args:
            order_id: The order number, for example "ORD-1042"
        '''
        return order_repository.find(order_id).status
"""

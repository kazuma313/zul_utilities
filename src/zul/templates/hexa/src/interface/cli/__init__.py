"""
Interface command line.

Gunanya:
    Menjalankan use case dari terminal: tugas terjadwal, impor data, atau
    mencoba agent tanpa menyalakan server.

Contoh:
    # interface/cli/chat.py  ->  python -m src.interface.cli.chat "halo"
    import sys

    from src.interface.http.controllers.chat_controller import get_chat_usecase

    if __name__ == "__main__":
        print(get_chat_usecase().execute(sys.argv[1], thread_id="cli"))
"""

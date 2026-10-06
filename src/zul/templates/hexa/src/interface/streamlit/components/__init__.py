"""
Potongan UI Streamlit yang dipakai ulang di beberapa halaman.

Contoh:
    # interface/streamlit/components/chat_history.py
    import streamlit as st

    def render_chat_history(messages: list[dict]) -> None:
        for message in messages:
            st.chat_message(message["role"]).write(message["content"])
"""

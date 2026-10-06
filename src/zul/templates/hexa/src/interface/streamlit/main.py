# Halaman utama: chatbot yang memanggil OpenAI langsung.
#
# Menjalankan dari root proyek:
#     streamlit run src/interface/streamlit/main.py
#
# Contoh bawaan Streamlit. API key diisi user di sidebar,
# dan riwayat percakapan disimpan di `st.session_state`.
#
# Untuk memakai agent proyek ini (bukan OpenAI langsung), panggil REST API:
#     import httpx
#     reply = httpx.post("http://localhost:8000/chat", json={"message": prompt}).json()
#     st.chat_message("assistant").write(reply["answer"])

import streamlit as st
from openai import OpenAI

with st.sidebar:
    openai_api_key = st.text_input(
        "OpenAI API Key", key="chatbot_api_key", type="password"
    )
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"

st.title("💬 Chatbot")
st.caption("🚀 A Streamlit chatbot powered by OpenAI")
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=st.session_state.messages
    )
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

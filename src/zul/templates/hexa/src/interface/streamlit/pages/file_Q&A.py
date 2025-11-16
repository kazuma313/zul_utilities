import streamlit as st

with st.sidebar:
    anthropic_api_key = st.text_input(
        "Anthropic API Key", key="file_qa_api_key", type="password"
    )

st.title("📝 File Q&A with Anthropic")
uploaded_file = st.file_uploader("Upload an article", type=("txt", "md"))
question = st.text_input(
    "Ask something about the article",
    placeholder="Can you give me a short summary?",
    disabled=not uploaded_file,
)

if uploaded_file and question and not anthropic_api_key:
    st.info("Please add your Anthropic API key to continue.")

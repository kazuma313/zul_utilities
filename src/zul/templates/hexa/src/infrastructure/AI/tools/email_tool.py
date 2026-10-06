"""
Contoh tool dengan efek ke dunia luar: mengirim email.

Gunanya:
    Placeholder untuk tool yang sebaiknya disetujui manusia sebelum
    dijalankan. Ganti isi fungsi dengan pengiriman sungguhan (SMTP,
    SendGrid, dan sejenisnya).

Cara pakai:
    from src.infrastructure.AI.tools.email_tool import send_email

    agent = build_human_in_the_loop_agent(
        llm=llm,
        tools=[send_email],
        tools_requiring_approval={send_email.name},
        checkpointer=checkpointer,
    )

Docstring fungsi dan bagian `Args` dikirim ke LLM sebagai deskripsi tool,
jadi tulis untuk dibaca model: jelas, spesifik, dan dalam bahasa Inggris
jika modelnya lebih baik di bahasa itu.
"""

import logging

from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient.

    Args:
        to: Email address of the recipient
        subject: Subject line of the email
        body: Plain-text content of the email
    """
    # Ini baru tempat penampung: emailnya hanya dicatat ke log, belum
    # dikirim. Ganti dengan pengiriman sungguhan lewat SMTP atau
    # layanan seperti SendGrid saat tool ini mulai dipakai.
    logger.info("send_email to=%s subject=%s", to, subject)

    return f"Email sent to {to} with subject '{subject}'"


tools = [send_email]

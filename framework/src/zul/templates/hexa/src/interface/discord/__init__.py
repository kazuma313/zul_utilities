"""
Interface bot Discord.

Gunanya:
    Menghubungkan use case chat ke Discord. Pakai id channel atau user
    sebagai `thread_id` supaya tiap percakapan punya memory sendiri.

Contoh (`pip install discord.py`):
    @client.event
    async def on_message(message):
        if message.author.bot:
            return
        answer = get_chat_usecase().execute(
            message.content, thread_id=str(message.channel.id)
        )
        await message.channel.send(answer)
"""

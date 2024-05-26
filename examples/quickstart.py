from teleapi.httpx_transport import httpx_teleapi_factory

bot = httpx_teleapi_factory("<BOT_TOKEN>", timeout=60)

offset = 0
while True:
    print("Waiting for updates...")
    updates = bot.getUpdates(offset=offset, timeout=50)
    for update in updates:
        bot.sendMessage(
            chat_id=update.message.chat.id,
            text="Yes " + (update.message.text or "??"),
        )
        offset = update.update_id + 1

import asyncio

from teleapi.httpx_transport import httpx_teleapi_factory_async

bot = httpx_teleapi_factory_async("<BOT_TOKEN>", timeout=60)


async def main():
    offset = 0
    while True:
        print("Waiting for updates...")
        updates = await bot.getUpdates(offset=offset, timeout=50)

        for update in updates:
            if update.message:
                await bot.sendMessage(
                    chat_id=update.message.chat.id,
                    text="Yes " + (update.message.text or "??"),
                )
            offset = update.update_id + 1


asyncio.run(main())

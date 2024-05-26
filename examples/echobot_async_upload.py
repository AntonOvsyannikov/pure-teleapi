import asyncio

from teleapi.httpx_transport import httpx_teleapi_factory_async

bot = httpx_teleapi_factory_async("<BOT_TOKEN>", timeout=60)


async def main():
    offset = 0
    while True:
        print("Waiting for updates...")
        updates = await bot.getUpdates(offset=offset, timeout=50)

        for update in updates:
            # httpx does not support aiofiles well :(
            # so one can use sync io here
            with open("tg.png", "rb") as f:
                await bot.sendPhoto(
                    chat_id=update.message.chat.id,
                    photo=f,
                )
            offset = update.update_id + 1


asyncio.run(main())

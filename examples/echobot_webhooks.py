import logging
import os

import uvicorn
from fastapi import FastAPI, Header

from teleapi.httpx_transport import httpx_teleapi_factory_async
from teleapi.teleapi import Update

# PLEASE READ FIRST!
# https://core.telegram.org/bots/webhooks
# also type `pip install fastapi, uvicorn` to run this example

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_URL = os.environ["HOST_URL"] + "/echobot"
WEBHOOK_SECRET_TOKEN = os.environ["SECRET_TOKEN"]

bot = httpx_teleapi_factory_async(BOT_TOKEN)

app = FastAPI()


@app.on_event("startup")
async def init_app():
    logging.basicConfig(level=logging.INFO)
    await bot.deleteWebhook()
    await bot.setWebhook(url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET_TOKEN)
    webhook_info = await bot.getWebhookInfo()
    logging.info(f"Webhook info after startup {webhook_info}")


@app.on_event("shutdown")
async def shutdown_app():
    await bot.deleteWebhook()
    webhook_info = await bot.getWebhookInfo()
    logging.info(f"Webhook info after shutdown {webhook_info}")


@app.get("/")
async def hello():
    return "Hello, I am echobot!"


@app.post("/echobot")
async def echobot(
    update: Update,
    secret_token: str = Header(alias="X-Telegram-Bot-Api-Secret-Token"),
):
    if secret_token != WEBHOOK_SECRET_TOKEN:
        logging.error(f"Invalid secret token {secret_token}")
        return

    if update.message:
        await bot.sendMessage(
            chat_id=update.message.chat.id,
            text="Yes " + (update.message.text or "??"),
        )


uvicorn.run(app, host="0.0.0.0")

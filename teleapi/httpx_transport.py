import json

import httpx

from teleapi.teleapi import Teleapi, TeleapiAsync
from teleapi.teleproxy import TeleProxy, TeleProxyAsync

# use with httpx extras !


class HttpxTeleTransport:
    def __init__(self, bot_token: str, telegram_api: str, timeout: int):
        self.bot_token = bot_token
        self.telegram_api = telegram_api
        self.timeout = timeout

    def request(self, api_method_name: str, params: dict, files: dict) -> dict:
        params = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in params.items()}
        resp = httpx.post(
            f"{self.telegram_api}bot{self.bot_token}/{api_method_name}",
            data=params,
            files=files,
            timeout=self.timeout,
        )

        # 400 response still contain valid ApiResponse with ok=False,
        # so TeleProxy raise TeleError with informative description
        if resp.status_code != 400:
            resp.raise_for_status()

        return resp.json()

    async def request_async(self, api_method_name: str, params: dict, files: dict) -> dict:
        params = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in params.items()}

        async with httpx.AsyncClient() as cli:
            resp = await cli.post(
                f"{self.telegram_api}bot{self.bot_token}/{api_method_name}",
                data=params,
                files=files,
                timeout=self.timeout,
            )
            if resp.status_code != 400:
                resp.raise_for_status()

            return resp.json()


def httpx_teleapi_factory(
    bot_token: str,
    telegram_api: str = "https://api.telegram.org/",
    timeout: int = 60,
) -> Teleapi:
    return TeleProxy(HttpxTeleTransport(bot_token, telegram_api, timeout))  # noqa


def httpx_teleapi_factory_async(
    bot_token: str,
    telegram_api: str = "https://api.telegram.org/",
    timeout: int = 60,
) -> TeleapiAsync:
    return TeleProxyAsync(HttpxTeleTransport(bot_token, telegram_api, timeout))  # noqa

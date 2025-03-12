# pure-teleapi
Pure declarative Telegram Bot API and implementation with Pydantic models 
and Protocol-based API definitions (both sync and async) with neat typehints and docstrings, 
generated directly from Telegram website docs, parser/generator is included.

## Motivation

Get tired of dozens telegram libs with strange json-parsing stuff
and a bunch of unnecessary bells and whistles? Me too, so please meet N+1th one.

No helpers, no handlers, no batteries included, only pure API models,
[pydantic](https://pypi.org/project/pydantic/)-based, which, I believe, is golden standard 
for json parsing/converting now,
abstract API protocols, fully typed and documented with well-formatted docstrings,
and just few of lines of python magic to make it work with any of
[requests](https://pypi.org/project/requests/)-like library,
[httpx](https://pypi.org/project/httpx/) implementation both sync and async is included as extra.

## Features

* Fully-generated from API [docs](https://core.telegram.org/bots/api) (Bot API 8.3 from Feb 12, 2025).
* Always is up-to-date, because parser/generator is included.
* Full set of `pydantic` models for all of Telegram API objects.
* Declarative protocols (both sync and async) for Telegram API methods.
* All with neat well-formatted docstrings, so no need to check website, everything is in code. 
* Compatible both with `pydantic` v1/v2.
* Can use any underlying `requests`-like lib, `httpx`-based implementation is included, both sync and async.
* Supports upload from ordinary file-like objects (IOBased) (relied on `files=` parameter of underlying lib).
* Async file io can be implemented by user.

## Installation

To install with ready to use `httpx`-based implementation type

```
pip install pure-teleapi[httpx]
```

To install with no external dependencies (except `pydantic`) 

```
pip install pure-teleapi
```

In this case it's a must to provide underlying transport, it's easy, just check [teleapi/httpx_transport.py](teleapi/httpx_transport.py).

## Quickstart

```
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
```


# Using parser/generator

If this lib becomes outdated, one can parse and generate updated version easily.

Clone repo, then type `poetry install --with dev --all-extras` and just run [apigen/__main__.py](apigen/__main__.py).

`teleapi.py` will appear in `.generated` dir, check then copy it to `teleapi` package.

Because docs are human readable, some sort of adoptions in parser may be necessary. 

Most difficulties are in parsing return type of the methods, 
so please check `apigen.models.ApiType.parse_return_type()` method.


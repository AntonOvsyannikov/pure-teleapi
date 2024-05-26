from io import IOBase
from typing import Union, get_type_hints

import pydantic
from pydantic import BaseModel

if pydantic.__version__.split(".")[0] == "1":
    from pydantic import parse_obj_as

    def to_dict(t, o):
        class M(BaseModel):
            __root__: t

        return M(__root__=o).dict(exclude_unset=True, by_alias=True)["__root__"]

else:
    from pydantic import TypeAdapter

    def parse_obj_as(t, o):
        return TypeAdapter(t).validate_python(o)

    def to_dict(t, o):
        return TypeAdapter(t).dump_python(o, exclude_unset=True)


from teleapi.teleapi import Teleapi
from teleapi.teletransport import ApiResponse, TeleTransport, TeleTransportAsync


class TeleError(Exception):
    def __init__(self, message: str, error_code: int):
        super().__init__(message)
        self.error_code = error_code


def _prepare_request(api_method_name: str, kwargs: dict, iobase):
    hints = get_type_hints(getattr(Teleapi, api_method_name))
    params = {k: to_dict(hints[k], v) for k, v in kwargs.items() if not isinstance(v, iobase)}
    files = {k: v for k, v in kwargs.items() if isinstance(v, iobase)}
    return hints, params, files


def _parse_response(resp: Union[ApiResponse, dict], hints: dict):
    if not isinstance(resp, ApiResponse):
        resp = parse_obj_as(ApiResponse, resp)

    if not resp.ok:
        raise TeleError(resp.description, resp.error_code or 0)

    return parse_obj_as(hints["return"], resp.result)


class TeleProxy:
    def __init__(self, transport: TeleTransport, iobase=IOBase):
        self.transport = transport
        self.iobase = iobase

    def __getattr__(self, api_method_name: str):
        def proxy(**kwargs):
            hints, params, files = _prepare_request(api_method_name, kwargs, self.iobase)
            resp = self.transport.request(api_method_name, params, files)
            return _parse_response(resp, hints)

        return proxy


class TeleProxyAsync:
    def __init__(self, transport: TeleTransportAsync, iobase=IOBase):
        self.transport = transport
        self.iobase = iobase

    def __getattr__(self, api_method_name: str):
        async def proxy(**kwargs):
            hints, params, files = _prepare_request(api_method_name, kwargs, self.iobase)
            resp = await self.transport.request_async(api_method_name, params, files)
            return _parse_response(resp, hints)

        return proxy

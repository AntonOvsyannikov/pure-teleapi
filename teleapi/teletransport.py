from typing import Any, Optional, Protocol, Union

from pydantic import BaseModel

from teleapi.teleapi import ResponseParameters


class ApiResponse(BaseModel):
    """
    The response contains a JSON object, which always has a Boolean field
    'ok' and may have an optional String field 'description' with a human-
    readable description of the result. If 'ok' equals True, the request
    was successful and the result of the query can be found in the
    'result' field. In case of an unsuccessful request, 'ok' equals false
    and the error is explained in the 'description'. An Integer
    'error_code' field is also returned, but its contents are subject to
    change in the future. Some errors may also have an optional field
    'parameters' of the type ResponseParameters, which can help to
    automatically handle the error.
    """

    ok: bool
    result: Optional[Any] = None
    description: Optional[str] = None
    error_code: Optional[int] = None
    parameters: Optional[ResponseParameters] = None


class TeleTransport(Protocol):
    def request(self, api_method_name: str, params: dict, files: dict) -> Union[ApiResponse, dict]:
        pass


class TeleTransportAsync(Protocol):
    async def request_async(self, api_method_name: str, params: dict, files: dict) -> Union[ApiResponse, dict]:
        pass

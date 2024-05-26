from io import StringIO

from teleapi.teleapi import Chat, Message, MessageEntity, Teleapi
from teleapi.teleproxy import TeleError, TeleProxy
from teleapi.teletransport import ApiResponse, TeleTransport

msg = Message(
    message_id=1,
    date=123,
    chat=Chat(
        id=2,
        type="private",
    ),
)


class TestTransportGood:
    def request(self, api_method_name: str, params: dict, _files: dict) -> ApiResponse:
        assert api_method_name == "sendMessage"
        assert params == {"chat_id": 123, "text": "msg", "entities": [{"type": "qq", "offset": 1, "length": 1}]}
        return ApiResponse(
            ok=True,
            result=msg.dict(),
        )


class TestTransportFile:
    def request(self, _api_method_name: str, _params: dict, files: dict) -> ApiResponse:
        assert files["photo"].read() == "foo"
        return ApiResponse(
            ok=True,
            result=msg,
        )


class TestTransportBad:
    def request(self, _api_method_name: str, _params: dict, _files: dict) -> dict:
        return {
            "ok": False,
            "description": "Some error",
            "error_code": 1,
        }


def factory(transport: TeleTransport) -> Teleapi:
    return TeleProxy(transport)  # noqa


api = factory(TestTransportGood())

assert api.sendMessage(chat_id=123, text="msg", entities=[MessageEntity(type="qq", offset=1, length=1)]) == msg

api = factory(TestTransportBad())

raised = False
try:
    api.sendMessage(
        chat_id=123,
        text="msg",
    )
except TeleError as e:
    raised = True
    assert str(e) == "Some error"

assert raised

api = factory(TestTransportFile())

f = StringIO("foo")
assert api.sendPhoto(chat_id=1, photo=f) == msg

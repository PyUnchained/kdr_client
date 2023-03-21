import json, websockets, asyncio, gzip
import ssl
import certifi
from copy import copy
import asyncio
from functools import wraps

from websockets.client import WebSocketClientProtocol
from websockets.exceptions import InvalidStatusCode, InvalidState

from kivy_django_restful.config.tools import get_settings_config
from .logging import write_to_log
from .urls import import_class
settings = get_settings_config()

class ServerErrorResponse(RuntimeError):
    pass

class ServerTimeoutResponse(RuntimeError):
    pass

class EmptyServerResponse(RuntimeError):
    pass

class BasicClientProtocol(WebSocketClientProtocol):

    def __init__(self, *args, **kwargs):
        kwargs['extra_headers'] = self.get_auth_headers()
        (super().__init__)(*args, **kwargs)

    async def handshake(self, *args, **kwargs):
        try:
            await super().handshake(*args, **kwargs)

        except InvalidStatusCode as e:

            request = args[0]
            if e.status_code == 500:
                write_to_log(
                    f"API rejected request (are you sure path exists?).\n"
                    f"Host: {request.host}\nPath: {request.path}\n"
                    f"Is Secure: {request.secure}", level='warning')

    def get_auth_headers(self):
        """
        Returns the headers used to authenticate with the server. We just
        need to prove that the request is coming from someone with the correct
        secret key.
        """
        header_getter = import_class(settings.WS_HEADER_GETTER)()
        return header_getter.get()

    def raise_error_for_msg(self, error, msg):
        error.msg = msg
        raise error

    async def recv(self, *args, **kwargs):

        # Perform the usual 'recv', but set a sane timeout
        try:
            msg = await asyncio.wait_for(
                (super().recv)(*args, **kwargs),
                timeout=(settings.WS_TIMEOUT)
            )


        # Handle any timeouts gracefully
        except asyncio.exceptions.TimeoutError:
            self.raise_error_for_msg(
                ServerTimeoutResponse(
                    f"Request Timed Out ({settings.WS_TIMEOUT}s)"),
                {}
            )

        return msg

class GzipClientProtocol(BasicClientProtocol):

    async def recv(self, *args, **kwargs):

        raw_json = await super().recv(*args, **kwargs)
        msg = json.loads(gzip.decompress(raw_json).decode())

        # Check the message returned to see if there are any errors associated with it
        if isinstance(msg, dict):
            if not msg.get('okay', True):
                self.raise_error_for_msg(
                    ServerErrorResponse(
                        f'Server Error\n{msg.get("msg", "")}'
                    ), msg
                )
        return msg

    async def send(self, content):
        packet = gzip.compress(json.dumps(content, indent=4).encode('utf-8'))
        await super().send(packet)
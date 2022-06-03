

import json, websockets, asyncio, gzip
import ssl
import certifi
from copy import copy
import asyncio

from websockets.client import WebSocketClientProtocol
from websockets.exceptions import InvalidStatusCode

from kivy_django_restful.config.tools import get_settings_config
from kivy_django_restful.utils import write_to_log
settings = get_settings_config()

class GzipClientProtocol(WebSocketClientProtocol):

    def __init__(self, *args, **kwargs):
        kwargs['extra_headers'] = self.get_auth_headers()
        (super().__init__)(*args, **kwargs)

    async def close(self, *args, **kwargs):
        try:
            await super().close(*args, **kwargs)

        # Caused when the connection is closed before it is openned
        # and gets to send data.
        except AttributeError: 
            pass



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

        from kivy_django_restful import kdr_applet
        headers = {'android-key': settings.ANDROID_SECRET_KEY}
        if kdr_applet.logged_in_user:
            headers['api_key'] = kdr_applet.logged_in_user.api_key
        return headers

    async def recv(self, *args, **kwargs):
        try:
            raw_json = await asyncio.wait_for(
                (super().recv)(*args, **kwargs),
                    timeout=(settings.WS_TIMEOUT)
            )
        except asyncio.exceptions.TimeoutError:
            write_to_log(f"Request Timeout.\n{args}\n{kwargs}", level='warning')
            return {}

        return json.loads(gzip.decompress(raw_json).decode())

    async def send(self, content):
        packet = gzip.compress(json.dumps(content, indent=4).encode('utf-8'))
        await super().send(packet)


class WebsocketConnectionFactory:

    @property
    def remote_ws_url(self):
        url_copy = copy(settings.REMOTE_URL)
        if 'https' in url_copy:
            replace_lookup = 'https'
            replace_with = 'wss'
        else:
            replace_lookup = "http"
            replace_with = 'ws'
        return url_copy.replace(replace_lookup, replace_with) + 'ws/'

    def open(self, endpoint):
        """ Open a new websocket connection. """

        # If the supplied endpoint doesn't include the base URL
        # include it in the path
        if any([x not in endpoint for x in ['ws://','wss://']]):
            endpoint = f"{self.remote_ws_url}{endpoint}"

        connection_kwargs = {'create_protocol':GzipClientProtocol}
        if not settings.DEBUG:
            connection_kwargs['ssl'] = ssl.create_default_context(
                cafile=certifi.where())

        return websockets.connect(endpoint, **connection_kwargs)
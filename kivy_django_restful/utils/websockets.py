import json, websockets, asyncio, gzip
import ssl
import certifi
from copy import copy
import asyncio
from functools import wraps

from websockets.client import WebSocketClientProtocol
from websockets.exceptions import InvalidStatusCode
from websockets.connection import OPEN

from kivy_django_restful.config.tools import get_settings_config
from kivy_django_restful.utils import write_to_log
settings = get_settings_config()

class GzipClientProtocol(WebSocketClientProtocol):

    def __init__(self, *args, **kwargs):
        kwargs['extra_headers'] = self.get_auth_headers()
        (super().__init__)(*args, **kwargs)

    # async def close(self, *args, **kwargs):
    #     try:
    #         await super().close(*args, **kwargs)

    #     # Caused when the connection is closed before it is openned
    #     # and gets to send data.
    #     except AttributeError:
    #         write_to_log(args, kwargs) 
    #         pass



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

    async def aopen(self, endpoint):
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

    def open(self, endpoint):
        """ Open a new websocket connection. """

        

        connection_kwargs = {'create_protocol':GzipClientProtocol}
        if not settings.DEBUG:
            connection_kwargs['ssl'] = ssl.create_default_context(
                cafile=certifi.where())

        return websockets.connect(endpoint, **connection_kwargs)

class managed_ws_conn(object):
    """ Decorator for safely passing multiple messages through as single
    websocket connection. """

    def __init__(self, endpoint):
        
        # If enpoint doesn't include root url, do so now
        if any([x not in endpoint for x in ['ws://','wss://']]):
            self.endpoint = f"{self.remote_ws_url}{endpoint}"
        else:
            self.endpoint = endpoint

    def __call__(self, fn):

        if not asyncio.iscoroutinefunction(fn):
            raise ValueError("This wrapper cannot be used with sync functions")


        @wraps(fn)
        async def async_decorated_fn(*args, **kwargs):
            conn = await self.create_connection()

            # Check that the connection is actually open. Don't run
            # wrapped code unless it is
            if conn.state != OPEN:
                return False

            result = await fn(*args, ws=conn, **kwargs)

            # Gracefully close if wrapped function didn't already
            if conn.state == OPEN:
                await conn.close()

            return result
        
        return async_decorated_fn

    @property
    def remote_ws_url(self):
        """ Return base websocket URL for remote server. """

        url_copy = copy(settings.REMOTE_URL)
        if 'https' in url_copy:
            replace_lookup = 'https'
            replace_with = 'wss'
        else:
            replace_lookup = "http"
            replace_with = 'ws'

        return url_copy.replace(replace_lookup, replace_with) + 'ws/'

    async def create_connection(self):
        connection_kwargs = {'create_protocol':GzipClientProtocol}

        # ssl context has to be explicitly declared to work with multiple archs
        if not settings.DEBUG:
            connection_kwargs['ssl'] = ssl.create_default_context(
                cafile=certifi.where())

        return await websockets.connect(self.endpoint, **connection_kwargs)
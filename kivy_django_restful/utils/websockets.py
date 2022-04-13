# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/utils/websockets.py
# Compiled at: 2022-04-03 12:45:32
# Size of source mod 2**32: 1696 bytes
from websockets.client import WebSocketClientProtocol
import json, websockets, asyncio, gzip
from kivy_django_restful.config.tools import get_settings_config
from kivy_django_restful.utils import write_to_log
settings = get_settings_config()

class GzipClientProtocol(WebSocketClientProtocol):

    def __init__(self, *args, **kwargs):
        kwargs['extra_headers'] = self.get_auth_headers()
        (super().__init__)(*args, **kwargs)

    def get_auth_headers(self):
        """
        Returns the headers used to authenticate with the server.
        * Note: All header keys should be lower case,
        i.e. 'api_key' not 'API_KEY'
        """
        from kivy_django_restful import kdr_applet
        headers = {'android-key': settings.ANDROID_SECRET_KEY}
        if kdr_applet.logged_in_user:
            headers['api_key'] = kdr_applet.logged_in_user.api_key
        return headers

    async def recv(self, *args, **kwargs):
        raw_json = await asyncio.wait_for((super().recv)(*args, **kwargs), timeout=(settings.WS_TIMEOUT))
        return json.loads(gzip.decompress(raw_json).decode())

    async def send(self, content):
        await super().send(gzip.compress(json.dumps(content, indent=4).encode('utf-8')))


class WebsocketConnectionFactory:

    def open(self, path):
        return websockets.connect(path, create_protocol=GzipClientProtocol)
# okay decompiling websockets.cpython-38.pyc

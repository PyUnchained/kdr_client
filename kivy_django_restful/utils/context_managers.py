from copy import copy
import ssl, certifi
import websockets, asyncio



class KDRBusyContext():
    def __init__(self, *args):
        from kivy_django_restful import kdr_applet
        self.applet = kdr_applet
        if not getattr(self.applet, 'busy_contexts', None):
            self.applet.busy_contexts = []
        self.applet.working = True

    def __enter__(self):
        self.applet.busy_contexts.append(self)

    def __exit__(self, type, value, traceback):
        self.applet.busy_contexts.remove(self)
        if self.applet.busy_contexts == []:
            self.applet.working = False

class WSConnectionContext():

    def __init__(self, protocol_class, endpoint):
        from kivy_django_restful import kdr_applet
        self.applet = kdr_applet
        self.protocol_class = protocol_class
        self.endpoint = endpoint

    @property
    def __remote_ws_url(self):
        # from kivy_django_restful.config.tools import get_settings_config
        # settings = get_settings_config()
        url_copy = copy(self.applet.settings.REMOTE_URL)
        if 'https' in url_copy:
            replace_lookup = 'https'
            replace_with = 'wss'
        else:
            replace_lookup = "http"
            replace_with = 'ws'
        return url_copy.replace(replace_lookup, replace_with) + 'ws/'

    async def __aenter__(self):
        # If the supplied endpoint doesn't include the base URL
        # include it in the path
        if any([x not in self.endpoint for x in ['ws://','wss://']]):
            self.endpoint = f"{self.__remote_ws_url}{self.endpoint}"

        connection_kwargs = {
            'create_protocol':self.protocol_class
        }
        if not self.applet.settings.DEBUG:
            connection_kwargs['ssl'] = ssl.create_default_context(
                cafile=certifi.where())
        self.ws = await websockets.connect(self.endpoint, **connection_kwargs)
        return self.ws

    async def __aexit__(self, exc_type, exc, tb):
        try:
            await self.ws.close()

        except AttributeError:
            pass

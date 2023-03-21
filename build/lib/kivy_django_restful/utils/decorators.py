import websockets
import asyncio
from functools import wraps

from .logging import write_to_log
from .context_managers import KDRBusyContext, WSConnectionContext
from .websockets import GzipClientProtocol, ServerErrorResponse, ServerTimeoutResponse, EmptyServerResponse

class managed_ws_conn(object):
    """ Decorator for safely passing multiple messages through as single
    websocket connection. """

    def __init__(self, endpoint, protocol=GzipClientProtocol):
        self.endpoint = endpoint
        self.protocol = protocol

    def __call__(self, fn):
    
        if not asyncio.iscoroutinefunction(fn):
            raise ValueError("This wrapper cannot be used with sync functions")

        @wraps(fn)
        async def async_decorated_fn(*args, **kwargs):
            from kivy_django_restful import kdr_applet

            with KDRBusyContext():
                async with WSConnectionContext(self.protocol, self.endpoint) as active_ws:
                    try:
                        resp = await fn(active_ws, kdr_applet, *args, **kwargs)
                        return 

                    except websockets.exceptions.InvalidStatusCode as e:
                        try:
                            write_to_log('Exception', level='warning', include_traceback=True)
                        finally:
                            e = None
                            del e

                    except websockets.exceptions.InvalidState as e:
                        write_to_log("",
                            level='warning', include_traceback=True)

                    except ServerTimeoutResponse as e:
                        write_to_log('', level='warning', include_traceback=True)

                    # Gracefully handle the case where the server has explicitly
                    # returned an error response message.
                    except ServerErrorResponse:
                        write_to_log(
                            'Connection closed prematurely. See the above trace '
                            'for more details.', level='warning', include_traceback=True)

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
        connection_kwargs = {'create_protocol':self.protocol}

        # ssl context has to be explicitly declared to work with multiple archs
        if not settings.DEBUG:
            connection_kwargs['ssl'] = ssl.create_default_context(
                cafile=certifi.where()
            )

        return await websockets.connect(self.endpoint, **connection_kwargs)
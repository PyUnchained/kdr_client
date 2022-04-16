import asyncio, json, websockets, django, pathlib
from django.core import management
from kivy_django_restful.resources.managers import ResourceManager
from kivy_django_restful.utils import import_class, write_to_log
from kivy_django_restful.utils.websockets import WebsocketConnectionFactory
from kivy_django_restful.notifications import NotificationManager
from pickle_storage.config.tools import ConfigObject
from kivy.event import EventDispatcher
from kivy.utils import platform
active_applet = None

class KDRApplet(EventDispatcher):
    __doc__ = ' Applet serves as the interface for interacting with all the\n    underlying Django machinery. '
    backend_path = 'kivy_django_restful.backends.tastypie.TastyPieBackend'

    def __init__(self, *args, **kwargs):
        django.setup()
        super().__init__()
        self._KDRApplet__logged_in_user = {}
        self.register_event_type('on_login_auth_accepted')
        self.register_event_type('on_login_auth_done')
        self.register_event_type('on_login_auth_rejected')
        self.ws_connection_factory = WebsocketConnectionFactory()
        self._backend = import_class(self.backend_path)(self)
        self.settings = ConfigObject(required_modules=[
         'kivy_django_restful.config.defaults'])
        self.resource_manager = ResourceManager(self)
        self.notification_manager = NotificationManager(self)

    async def detect_setup(self):
        """ Check whether the database file has already been created or not. """

        await asyncio.sleep(5)
        path_to_db = pathlib.Path(self.settings.BASE_DIR, self.settings.DB_NAME)
        if not path_to_db.exists():
            write_to_log('Detecting', level='error')
            self.notification_manager.debug_message(
                'Hi!\nThank-you for installing the app. Please wait a few seconds to '
                'properly configure the database.\n\nWe only need to do this once.')
            self.setup()



    async def async_login(self, username, password):
        if not username or not password:
            self.notification_manager.debug_message(f'Please enter username and password')
            return

        self.notification_manager.debug_message(f'attempting to login as "{username}"')
        try:
            async with self.ws_connection_factory.open(f"{self.settings.REMOTE_WS_URL}login") as ws:
                await ws.send({'username':username,  'password':password,  'type':'auth'})
                msg = await ws.recv()
                if msg['okay']:
                    self.dispatch('on_login_auth_accepted', username)
                    await ws.send({'type': 'login_data'})
                    expected = await ws.recv()
                    self.notification_manager.debug_message('Waiting for data...')
                    for i, name in enumerate(expected):
                        data = await ws.recv()
                        await self.resource_manager.load_data((data['resource_name']),
                          (data['data']), index=i,
                          total=expected)
                    else:
                        self.dispatch('on_login_auth_done')

                else:
                    self.dispatch('on_login_auth_rejected')
        except websockets.exceptions.InvalidStatusCode as e:
            try:
                write_to_log('Exception', level='warning', include_traceback=True)
            finally:
                e = None
                del e

    @property
    def logged_in_user(self):
        """ Returns a dictionary representing the current logged in user,
        otherwise 'None'. """
        return self._KDRApplet__logged_in_user

    def on_login_auth_accepted(self, username):
        self.notification_manager.debug_message(f'logged in as "{username}"')

    def on_login_auth_done(self):
        pass

    def on_login_auth_rejected(self):
        pass

    # def setup(self):
    #     if platform != 'android':
    #         management.call_command('makemigrations')
    #     management.call_command('migrate', no_input=True)

    def set_logged_in_user(self, username, api_key):
        self._KDRApplet__logged_in_user = {'username':username, 
         'api_key':api_key}
# okay decompiling applet.cpython-38.pyc

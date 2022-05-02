import asyncio, json, websockets, django, pathlib
from asgiref.sync import sync_to_async
from django.core import management
from django.contrib.auth import get_user_model

from kivy_django_restful.resources.managers import ResourceManager
from kivy_django_restful.utils import import_class, write_to_log, TerminalNotificationStream
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
        self.register_event_type('on_data_loaded')
        self.register_event_type('on_logout')
        self.ws_connection_factory = WebsocketConnectionFactory()
        self._backend = import_class(self.backend_path)(self)
        self.settings = ConfigObject(required_modules=[
         'kivy_django_restful.config.defaults'])
        self.resource_manager = ResourceManager(self)
        self.notification_manager = NotificationManager(self)

    @property
    def nm(self):
        return self.notification_manager

    async def detect_setup(self):
        """ Check whether the database tabl. """
        await asyncio.sleep(.2)
        if self.settings.DEBUG and platform != 'android':
            await sync_to_async(management.call_command)('makemigrations')
            await sync_to_async(management.call_command)('migrate')

        try:
            await sync_to_async(management.call_command)('migrate', check=True)
        except:

            # Send user feedback on what we're up to
            seconds_to_wait = 3
            for i in range(seconds_to_wait):
                seconds_left = seconds_to_wait - i
                self.notification_manager.debug_message(
                    'Please wait a few seconds while we '
                    'configure your database.\n\n'
                    f'Starting in {seconds_left} ...', timeout=seconds_to_wait)
                await asyncio.sleep(1)

            await self.setup()



    async def async_login(self, username, password, *args, wait=0, new_account=False):
        await asyncio.sleep(wait)

        if not username or not password:
            self.notification_manager.debug_message(f'Please enter username and password')
            return

        self.notification_manager.debug_message(f'Logging in as {username}')
        try:
            async with self.ws_connection_factory.open(f"{self.settings.REMOTE_WS_URL}auth") as ws:
                await ws.send({'username':username,  'password':password,  'type':'auth'})
                msg = await ws.recv()
                if msg['okay']:
                    self.dispatch('on_login_auth_accepted', username,
                        new_account=new_account)
                    await ws.send({'type': 'login_data'})
                    expected = await ws.recv()
                    self.notification_manager.debug_message('Waiting for data...')
                    for i, name in enumerate(expected):
                        data = await ws.recv()
                        await self.resource_manager.load_data((data['resource_name']),
                          (data['data']), index=i, total=len(expected))
                    else:
                        self.dispatch('on_login_auth_done')

                else:
                    self.dispatch('on_login_auth_rejected', msg.get('msg', None))
        except websockets.exceptions.InvalidStatusCode as e:
            try:
                write_to_log('Exception', level='warning', include_traceback=True)
            finally:
                e = None
                del e

    async def async_logout(self, *args):
        await sync_to_async(management.call_command)('flush', no_input=True,
            interactive=False)
        self.dispatch('on_logout')

    @property
    def logged_in_user(self):
        """ Returns a dictionary representing the current logged in user,
        otherwise 'None'. """
        return self._KDRApplet__logged_in_user

    def on_login_auth_accepted(self, username, *args, new_account=False):
        self.notification_manager.debug_message(f'Logged in as "{username}"')

    def on_login_auth_done(self):
        pass

    def on_logout(self, *args):
        write_to_log('called')

    def on_data_loaded(self, *args):
        pass

    def on_login_auth_rejected(self, *args):
        pass

    async def setup(self):
        if platform != 'android':
            await sync_to_async(management.call_command)('makemigrations')
        with TerminalNotificationStream(self, timeout=20) as f:
            await sync_to_async(management.call_command)('migrate',
                no_input=True, stdout=f)
        self.notification_manager.debug_message('Database: OK', timeout=5)

    def set_logged_in_user(self, username, api_key):
        self._KDRApplet__logged_in_user = {'username':username, 
         'api_key':api_key}

import asyncio, json, websockets, pathlib, pickle
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.utils import platform

from pickle_storage.config.tools import get_settings_config

from kivy_django_restful.utils import import_class, write_to_log, TerminalNotificationStream
from kivy_django_restful.utils.data_sync import deserialize_data
from kivy_django_restful.models.registers import CreationRegister, UpdateRegister
from kivy_django_restful.utils.decorators import managed_ws_conn

active_applet = None

class KDRApplet(EventDispatcher):
    __doc__ = ' Applet serves as the interface for interacting with all the\n    underlying Django machinery. '
    backend_path = 'kivy_django_restful.backends.tastypie.TastyPieBackend'

    def __init__(self, *args, **kwargs):

        self.working = False
        self.db_ready = True
        self.suppressed_caches = []
        self._silence_signals = False
        super().__init__()
        self._KDRApplet__logged_in_user = {}
        self.register_event_type('on_login_auth_accepted')
        self.register_event_type('on_user_data_fetched')
        self.register_event_type('on_login_auth_rejected')
        self.register_event_type('on_data_loaded')
        self.register_event_type('on_login_complete')
        self.register_event_type('on_logout')
        self.register_event_type('on_user_data_fetch_error')
        self.register_event_type('on_db_changed')
        self._backend = import_class(self.backend_path)(self)
        self.settings = get_settings_config(
            required_modules=['kivy_django_restful.config.defaults'])
        self.notification_manager = None
        self.known_registers = {
            'create':CreationRegister, 'update':UpdateRegister}
        
        self.bind_notification_manager()
        # Clock.schedule_once(self.start_activating_registers, 3)

    def silence_orm_signals(self):
        applet = self

        class silence_signals_context_manager():

            def __enter__(self):
                """Start a new timer as a context manager"""
                applet._silence_signals = True
                return self

            def __exit__(self, *exc_info):
                """Stop the context manager timer"""
                applet._silence_signals = False

        return silence_signals_context_manager()

    @property
    def nm(self):
        return self.notification_manager
        
    async def async_logout(self, *args):
        self.dispatch('on_logout')        

    async def activate_registers(self, *register_classes):
        self.active_registers = []
        if self.settings.DEBUG and platform != 'android':
            wait_time = 1
        else:
            wait_time = 5
        await asyncio.sleep(wait_time)

        for reg_cls in register_classes:
            register = reg_cls(self)
            self.active_registers.append(register)

    async def async_update_register(self, name, instance):
        reg_cls = self.known_registers.get(name)
        if not reg_cls:
            write_to_log(f'Could not find requested register: "{name}"',
                level='warning')
            return

        for reg in self.active_registers:
            if isinstance(reg, reg_cls):
                await reg.async_add_instance(instance)
                break

    async def open_ws(self, path):
        return self.ws_connection_factory.open(f"{self.settings.REMOTE_WS_URL}{path}")

    async def upload_logs(self, *args, wait=0):
        await asyncio.sleep(wait)

        async with self.ws_connection_factory.open(
            f"{self.settings.REMOTE_WS_URL}app_sync") as ws:
                log_str = ''
                for log_file in self.settings.LOGFILE.parents[0].glob("*.log"):
                    log_str += self.settings.LOGFILE.read_text() + '\n'
                await ws.send({'username':self.username, 'type':'logs',
                    'log_text':log_str})
                self.nm.debug_message('Log information sent.', level='success')

    def bind_notification_manager(self, *args, **kwargs):
        manager_class = import_class(self.settings.NOTIFICATION_MANAGER_CLASS)
        self.notification_manager = manager_class(self)


    @property
    def logged_in_user(self):
        """ Returns a dictionary representing the current logged in user,
        otherwise 'None'. """
        return self._KDRApplet__logged_in_user

    def on_login_auth_accepted(self, username, *args, new_account=False):
        self.notification_manager.debug_message(f'Logged in as "{username}"')

    def on_user_data_fetched(self, *args, **kwargs):

        # There should be an explicitly defined class to handle all this
        handler_cls = import_class(
            self.settings.DEFAULT_APPLET_EVENT_LISTENERS['on_user_data_fetched']
        )
        handler_cls().handle(*args, **kwargs)

    def on_db_changed(self, *args, **kwargs):
        pass

    def on_user_data_fetch_error(self, *args, **kwargs):
        """ Dispatched event hook. """
        pass

    def on_logout(self, *args):
        """ Dispatched event hook. """
        pass

    def on_data_loaded(self, *args):
        """ Dispatched event hook. """
        pass

    def on_login_complete(self, *args, **kwargs):
        pass

    def on_login_auth_rejected(self, *args):
        """ Dispatched event hook. """
        pass

    def set_logged_in_user(self, username, api_key):
        self._KDRApplet__logged_in_user = {'username':username, 
            'api_key':api_key}

    def start_activating_registers(self, *args):
        asyncio.create_task(
            self.activate_registers(CreationRegister, UpdateRegister)
            )

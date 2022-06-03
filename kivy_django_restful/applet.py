import asyncio, json, websockets, django, pathlib
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.utils import platform

from pickle_storage.config.tools import ConfigObject
from asgiref.sync import sync_to_async
from django.core import management
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.apps import apps

from kivy_django_restful.resources.managers import ResourceManager
from kivy_django_restful.utils import import_class, write_to_log, TerminalNotificationStream
from kivy_django_restful.utils.data_sync import deserialize_data
from kivy_django_restful.utils.websockets import WebsocketConnectionFactory
from kivy_django_restful.notifications import NotificationManager
from kivy_django_restful.models.registers import CreationRegister, UpdateRegister
from kivy_django_restful.utils.context_managers import KDRBusyContext

active_applet = None

class KDRApplet(EventDispatcher):
    __doc__ = ' Applet serves as the interface for interacting with all the\n    underlying Django machinery. '
    backend_path = 'kivy_django_restful.backends.tastypie.TastyPieBackend'

    def __init__(self, *args, **kwargs):
        django.setup()
        self.working = False
        self.db_ready = True
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
        self.known_registers = {'create':CreationRegister,
            'update':UpdateRegister}
        
        Clock.schedule_once(self.start_activating_registers, 3)

    @property
    def nm(self):
        return self.notification_manager

    async def async_login(self, username, password, *args, wait=0, new_account=False):
        
        await asyncio.sleep(wait)
        if not self.db_ready:
            asyncio.create_task(self.async_login(
                username, password, *args, wait=5, new_account=new_account))
            return


        if not username or not password:
            self.nm.debug_message(f'Please enter username and password')
            return

        self.nm.debug_message(f'Logging in as {username}')
        try:
            async with self.ws_connection_factory.open(f"{self.settings.REMOTE_WS_URL}auth") as ws:
                await ws.send({'username':username,  'password':password,  'type':'auth'})

                with KDRBusyContext(self):
                    msg = await ws.recv()
                    if msg == {}:
                        self.nm.generic_error_message()
                        self.working = False
                        return

                    if msg.get('okay', False):
                        self.dispatch('on_login_auth_accepted', username,
                            new_account=new_account)
                        await ws.send({'type': 'login_data'})
                        expected = await ws.recv()
                        self.nm.debug_message('Fetching data from server...')
                        for i, name in enumerate(expected):
                            data = await ws.recv()
                            await self.resource_manager.load_data(
                                data.get('resource_name', None),
                                data.get('data', []),
                                index=i, total=len(expected)
                            )
                        else:
                            self.dispatch('on_login_auth_done')

                    else:
                        self.dispatch('on_login_auth_rejected',
                            msg.get('msg', 'Login Rejected'))
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

    async def async_sync_data(self, *args):
        data_to_sync = {'update':[], 'create':[], 'delete':[]}
        update_model_order = ['tsuro_app.doe', 'tsuro_app.sire', 'tsuro_app.litter',
            'tsuro_app.weanergroup', 'tsuro_app.death']

        async with await self.open_ws('app_sync') as ws:

            await ws.send({'type':'sync_full', 'username':self.username})

            # Loop over all the data sent from the remote
            self.remote_working = True
            while self.remote_working:
                try:
                    data = await ws.recv()
                    if not data:
                        self.remote_working = False
                        continue

                    action = data.get('action', None)
                    if not action:
                        continue

                    data_to_sync[action].extend(
                        json.loads(data['data']))
                    
                except ConnectionClosedOK:
                    self.remote_working = False
                except ConnectionClosed:
                    self.remote_working = False

        # Means that there isn't any data worth updating, stpo here
        if not any([data_to_sync[key] for key in data_to_sync]):
            return

        User = get_user_model()
        user_list = await sync_to_async(list)(User.objects.all())
        if not user_list:
            return
        else:
            user = user_list[0]

        # We'll later want to report to the server which records were commited
        committed_to_db = {'create':[], 'update':[], 'delete':[]}

        # Handling records that have been created and updated is the same process,
        # but we always want to do the creation step first
        for action in ['create', 'update']:
            data_list = data_to_sync.get(action, None)
            if not data_list:
                continue

            for model in update_model_order:
                for entry in data_list:
                    if entry['model'] != model:
                        continue

                    try:
                        await deserialize_data(entry, user=user)
                        committed_to_db[action].append(entry['pk'])
                    except:
                        write_to_log(f'Failed to save record from remote {action}',
                            level='warning', include_traceback=True)
        # Means that there isn't any data worth updating, stpo here
        if any([committed_to_db[key] for key in committed_to_db]):
            write_to_log('Date synced to server.')
        async with await self.open_ws('app_sync') as ws:
            await ws.send({
                'type':'sync_full_committed',
                'username':self.username,
                'committed_to_db':committed_to_db})



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

    @property
    def logged_in_user(self):
        """ Returns a dictionary representing the current logged in user,
        otherwise 'None'. """
        return self._KDRApplet__logged_in_user

    def on_login_auth_accepted(self, username, *args, new_account=False):
        self.notification_manager.debug_message(f'Logged in as "{username}"')

    def on_login_auth_done(self):
        """ Dispatched event hook. """
        pass

    def on_logout(self, *args):
        """ Dispatched event hook. """
        pass

    def on_data_loaded(self, *args):
        """ Dispatched event hook. """
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

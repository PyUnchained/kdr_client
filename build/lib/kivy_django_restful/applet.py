import asyncio, json, websockets, pathlib, pickle
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.utils import platform

from pickle_storage.config.tools import get_settings_config

from kivy_django_restful.utils import import_class, write_to_log, TerminalNotificationStream
from kivy_django_restful.utils.data_sync import deserialize_data
from kivy_django_restful.notifications import NotificationManager
from kivy_django_restful.models.registers import CreationRegister, UpdateRegister
from kivy_django_restful.utils.decorators import managed_ws_conn
from kivy_django_restful.ws_requests.login import ws_request_login

active_applet = None

class KDRApplet(EventDispatcher):
    __doc__ = ' Applet serves as the interface for interacting with all the\n    underlying Django machinery. '
    backend_path = 'kivy_django_restful.backends.tastypie.TastyPieBackend'

    def __init__(self, *args, **kwargs):

        self.working = False
        self.db_ready = True
        super().__init__()
        self._KDRApplet__logged_in_user = {}
        self.register_event_type('on_login_auth_accepted')
        self.register_event_type('on_user_data_fetched')
        self.register_event_type('on_login_auth_rejected')
        self.register_event_type('on_data_loaded')
        self.register_event_type('on_login_complete')
        self.register_event_type('on_logout')
        self.register_event_type('on_user_data_fetch_error')
        self._backend = import_class(self.backend_path)(self)
        self.settings = get_settings_config(
            required_modules=['kivy_django_restful.config.defaults'])
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

        await ws_request_login(new_account=new_account,
            **{'username':username,  'password':password})
    # @managed_ws_conn("auth")
    # async def ws_request_login(self, ws, *args, **kwargs):
    #     await ws.send({'type':'auth'} | kwargs)
    #     msg = await ws.recv()
    #     if msg == {}:
    #         self.nm.generic_error_message()
    #         self.working = False
    #         return

    #     if msg.get('okay', False):
    #         self.dispatch(
    #             'on_login_auth_accepted', username,
    #             new_account=new_account)
    #         self.nm.debug_message('Fetching data from server...')

    #         # Get the number of items we can expect to receive
    #         await ws.send({'type': 'login_data'})
    #         expected = await ws.recv()
    #         retrieved_data = []

    #         # retrieved_data stored locally
    #         if self.settings.CACHE_LOGIN_DATA:
    #             debug_data_path = pathlib.Path(
    #                 self.settings.BASE_DIR,'debug_init.json')

                
    #             try:
    #                 with debug_data_path.open('rb') as f:
    #                     data = pickle.load(f) or []
    #                     if data:
    #                         retrieved_data = data
    #             except (FileNotFoundError, EOFError):
    #                 pass

    #             except:
    #                 write_to_log('Error', level='warning',
    #                     include_traceback=True)


    #         # Retrieve and store each chunk of data.
    #         if retrieved_data == []:
    #             for i, name in enumerate(expected):
    #                 data = await ws.recv()
    #                 if data:
    #                     self.nm.debug_message(
    #                         f"{data['resource_name']} [OK]")
    #                     retrieved_data.append(data)

            
    #         if len(retrieved_data) == len(expected):
    #             self.dispatch(
    #                 'on_user_data_fetched', retrieved_data)

    #             # Write retrieved data for later
    #             if self.settings.CACHE_LOGIN_DATA:
    #                 debug_data_path = pathlib.Path(
    #                     self.settings.BASE_DIR,'debug_init.json')
                    
    #                 with debug_data_path.open('wb') as f:
    #                     try:
    #                         pickle.dump(retrieved_data, f)
    #                     except:
    #                         write_to_log('Error', level='warning',
    #                             include_traceback=True)
    #         else:
    #             self.dispatch(
    #                 'on_user_data_fetch_error',
    #                 expected, retrieved_data)

    #     else:
    #         self.dispatch('on_login_auth_rejected',
    #             msg.get('msg', 'Login Rejected'))

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

    async def async_sync_data(self, delay=0, *args, **kwargs):
        await asyncio.sleep(delay)
        write_to_log('### DEPRECATED', level='debug')
        # data_to_sync = {'update':[], 'create':[], 'delete':[]}
        # update_model_order = ['tsuro_app.doe', 'tsuro_app.sire', 'tsuro_app.litter',
        #     'tsuro_app.weanergroup', 'tsuro_app.death']

        # async with await self.open_ws('app_sync') as ws:

        #     await ws.send({'type':'sync_full', 'username':self.username})

        #     # Loop over all the data sent from the remote
        #     self.remote_working = True
        #     while self.remote_working:
        #         try:
        #             data = await ws.recv()
        #             if not data:
        #                 self.remote_working = False
        #                 continue

        #             action = data.get('action', None)
        #             if not action:
        #                 continue

        #             data_to_sync[action].extend(
        #                 json.loads(data['data']))
                    
        #         except ConnectionClosedOK:
        #             self.remote_working = False
        #         except ConnectionClosed:
        #             self.remote_working = False

        # # Means that there isn't any data worth updating, stpo here
        # if not any([data_to_sync[key] for key in data_to_sync]):
        #     return

        # User = get_user_model()
        # user_list = await sync_to_async(list)(User.objects.all())
        # if not user_list:
        #     return
        # else:
        #     user = user_list[0]

        # # We'll later want to report to the server which records were commited
        # committed_to_db = {'create':[], 'update':[], 'delete':[]}

        # # Handling records that have been created and updated is the same process,
        # # but we always want to do the creation step first
        # for action in ['create', 'update']:
        #     data_list = data_to_sync.get(action, None)
        #     if not data_list:
        #         continue

        #     for model in update_model_order:
        #         for entry in data_list:
        #             if entry['model'] != model:
        #                 continue

        #             try:
        #                 await deserialize_data(entry, user=user)
        #                 committed_to_db[action].append(entry['pk'])
        #             except:
        #                 write_to_log(f'Failed to save record from remote {action}',
        #                     level='warning', include_traceback=True)
        # # Means that there isn't any data worth updating, stpo here
        # if any([committed_to_db[key] for key in committed_to_db]):
        #     write_to_log('Date synced to server.')
        # async with await self.open_ws('app_sync') as ws:
        #     await ws.send({
        #         'type':'sync_full_committed',
        #         'username':self.username,
        #         'committed_to_db':committed_to_db})



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

    def on_user_data_fetched(self, *args, **kwargs):
        """ Dispatched event hook. """
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

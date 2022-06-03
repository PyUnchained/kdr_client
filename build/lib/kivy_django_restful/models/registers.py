import asyncio
from asgiref.sync import sync_to_async
import json
import pathlib
import websockets
import datetime

from kivy.utils import platform
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.event import EventDispatcher

from django.core import serializers
from pickle_storage.container import BaseStorageContainer

from kivy_django_restful.utils import write_to_log, log_async_errors
from kivy_django_restful.config import settings
from kivy_django_restful.utils.context_managers import KDRBusyContext
from kivy_django_restful.utils.serialize import CustomJsonEncoder

class BaseRegister(EventDispatcher):
    """ Registers are responsible for monitoring the state of """
    field_name = ''

    def __init__(self, applet, *args, **kwargs):
        self.fail_sync_counter = 0
        self.working = False
        self.applet = applet
        if not self.exists():
            self._write_to_file([])

        if self.applet.settings.DEBUG and platform != 'android':
            check_interval = 2
        else:
            check_interval = 10

        Clock.schedule_interval(self.check_for_updates, check_interval)



    @property
    def path_to_file(self):
        return pathlib.Path(settings.BASE_DIR, self.field_name)

    def _pause(self, *args, duration=60):
        self.working = True
        Clock.schedule_once(self._un_pause, duration)

    def _un_pause(self, *args):
        self.working = False
        self.fail_sync_counter = 0

    def _read_from_file(self):
        try:
            with self.path_to_file.open('r') as f:
                contents = json.loads(f.read())
            return contents

        # If we can't read from the file, we'll assume it's
        # corrupted and just start afresh
        except json.decoder.JSONDecodeError:
            self._write_to_file([])
            return []

    def _write_to_file(self, data_list):
        try:
            if not isinstance(data_list, list):
                write_to_log('Cannot save this content. Must be a list')
                return False

            with self.path_to_file.open('w') as f:
                f.write(json.dumps(data_list))
            return True
        except:
            write_to_log('Error writting to register file.',
                level='error')

    @log_async_errors
    async def async_add_instance(self, instance):
        # Ideally, all models should have a tracker, so we only serialize the fields
        # that have changed. If not, just do all of them
        data = await sync_to_async(serializers.serialize,
            thread_sensitive=False)("json",[instance], cls=CustomJsonEncoder)
        try:
            register_data = self._read_from_file()
            register_data.append(data)
            self._write_to_file(register_data)
        except:
            write_to_log('Failed to add to register.', level='error')


    async def async_perform_update(self, recent_updates, *args):
        raise NotImplementedError()   

    async def async_update_with_remote(self, recent_updates, *args, **kwargs):
        self.working = True
        try:
            await self.async_perform_update(recent_updates)
        except:
            write_to_log("Exception Occured",
                level='error')
        finally:
            self.working = False

    def check_for_updates(self, *args):
        # Means register is already trying to update the remote server
        if self.working:
            return

        if self.fail_sync_counter >= 3:
            self._pause()
            return
        
        try:
            recent_updates = self._read_from_file()
            if len(recent_updates) > 0:
                asyncio.create_task(
                    self.async_update_with_remote(recent_updates)
                )

        except FileNotFoundError:
            self._write_to_file([])

        except:
            write_to_log('Something seems amiss.', level='error')

    def exists(self):
        return pathlib.Path(settings.BASE_DIR, self.field_name).exists()

    async def async_perform_update(self, recent_updates):
        try:

            async with self.applet.ws_connection_factory.open(
                f"{settings.REMOTE_WS_URL}app_sync") as ws:

                with KDRBusyContext(self.applet):
                    failed_to_sync = []

                    for chunk in recent_updates:
                        await ws.send({'data':chunk,
                            'type':self.ws_request_type})
                        resp = await ws.recv()

                        # Determine whether or not chunk needs to be retried
                        if resp == {} or not resp.get('okay', False):
                            failed_to_sync.append(chunk)

                        # Implement suggested fixes from the server, if any
                        missing_fk_field = resp.get('missing_fk', None)
                        if any([missing_fk_field]):
                            for item in serializers.deserialize('json', chunk):
                                obj = item
                        else:
                            obj = None

                        if missing_fk_field:
                            await self.async_update_missing_fk(ws, obj.object,
                                missing_fk_field)


            if failed_to_sync:
                self.fail_sync_counter += 1
            self._write_to_file(failed_to_sync)

        except websockets.exceptions.InvalidStatusCode as e:
            self.fail_sync_counter += 1
            try:
                write_to_log('Exception', level='warning', include_traceback=True)
            finally:
                e = None
                del e

    async def async_update_missing_fk(self, ws, obj, field_name):
        if not obj:
            return

        missing_obj = await sync_to_async(getattr)(obj, field_name)
        data = await sync_to_async(serializers.serialize)(
            'json', [missing_obj], cls=CustomJsonEncoder)
        await ws.send({'data':data, 'type':'missing_fk'})



class CreationRegister(BaseRegister):
    field_name = 'created_on_app'
    ws_request_type = 'create'

class UpdateRegister(BaseRegister):
    field_name = 'update_remote'
    ws_request_type = 'update'



    
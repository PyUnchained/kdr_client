import json, uuid, contextlib, pathlib, asyncio
from asgiref.sync import sync_to_async
from sqlite3 import dbapi2 as Database
from django.db.utils import IntegrityError
from django.core import management
from django.core import serializers
import django.apps as apps
from django.db import connections
from kivy_django_restful.utils import (write_to_log, get_user_data_dir,
    TerminalNotificationStream, get_settings_config, TimedContext)
settings = get_settings_config()

@contextlib.contextmanager
def create_tmp_file(content):
    file_name = str(uuid.uuid4()) + '.json'
    path = pathlib.Path(settings.BASE_DIR, file_name)
    with open(path, 'w') as f:
        f.write(content)
    try:
        yield path
    finally:
        path.unlink()


class ResourceManager:
    __doc__ = ' Resource manager for '

    def __init__(self, applet):
        self.applet = applet
        self._deffered_data = []

    async def load_data(self, name, data, index=None, total=None):
        """ Takes Resource JSON and loads it into the DB. Django fixtures can be...
        tempramental, so we want to make sure we're received all of the packets
        we were expecting before runnin the loaddata command """

        if name != None and data != []:
            data = await self.clean_data(name, json.loads(data))
            self._deffered_data.extend(data)
            self.applet.notification_manager.debug_message(f"{name} data found [{len(data)}].")

        if index == total-1:
            await self.write_data()
                

    async def write_data(self):
        self.applet.notification_manager.debug_message(
            f"All Data Found.\n\nWritting to database.\n"
            "(May take 1-2 min if you have a lot of records) ",
                level='success', timeout=120)

        # We need to modify the data slightly before loading it into the database
        for item in self._deffered_data:
            if 'tsuro_auth.systemuser' == item['model']:
                item['pk'] = item['fields']['remote_pk']

        with TimedContext(name='Writing Data'):
            with create_tmp_file(json.dumps(self._deffered_data)) as tmp_path:
                try:
                    await sync_to_async(management.call_command)(
                        'loaddata', str(tmp_path))
                    self.applet.notification_manager.debug_message(f"Data Saved",
                        level='success')
                    self.applet.dispatch('on_data_loaded')

                except IntegrityError as e:
                    write_to_log(e, level='error')           


    async def clean_data(self, name, data):
        from tsuro_app.models import Doe, Litter, WeanerGroup, Causes

        # if name == 'TaskTracker':
        #     doe_list = await sync_to_async(list)(Doe.objects.all())
        #     litter_list = await sync_to_async(list)(Litter.objects.all())
        #     wg_list = await sync_to_async(list)(WeanerGroup.objects.all())

        #     tt_field_name_to_list = {'mate_does':doe_list, 'pregnancy_does':doe_list,
        #         'box_does':doe_list, 'wean_litters':litter_list,
        #         'harvest_weaners':wg_list}

        #     tt_list = []
        #     for tt in data:
        #         for tt_field_name in ['mate_does', 'pregnancy_does', 'box_does',
        #             'wean_litters', 'harvest_weaners']:

        #             missing_pks = []
        #             for target_pk in tt['fields'][tt_field_name]:
        #                 pk_found = False
        #                 for test_obj in tt_field_name_to_list[tt_field_name]:
        #                     if test_obj.pk == target_pk:
        #                         pk_found = True
        #                         break

        #                 if not pk_found:
        #                     missing_pks.append(target_pk)

        #             if missing_pks:
        #                 for pk_to_remove in missing_pks:
        #                     tt['fields'][tt_field_name].remove(pk_to_remove)

        #         tt_list.append(tt)
        #     data = json.dumps(tt_list)

        if name == 'Death':
            death_list = []
            cause_list = await sync_to_async(list)(Causes.objects.all())
            for death in data:
                for c in cause_list:
                    if c.pk == death['fields']['common_cause']:
                        death_list.append(death)
                        break
            
            data = json.dumps(death_list)

        if type(data) == str:
            data = json.loads(data)
        return data


        

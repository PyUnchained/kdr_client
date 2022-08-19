import json, uuid, contextlib, pathlib, asyncio

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
        write_to_log('### DEPRECATED', level='debug')      


    async def clean_data(self, name, data):
        write_to_log('### DEPRECATED', level='debug') 
        return data


        

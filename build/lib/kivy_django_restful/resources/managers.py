# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/resources/managers.py
# Compiled at: 2022-04-08 13:52:25
# Size of source mod 2**32: 1619 bytes
import json, uuid, contextlib, pathlib
from asgiref.sync import sync_to_async
from sqlite3 import dbapi2 as Database
from django.db.utils import IntegrityError
from django.core import management
from django.core import serializers
import django.apps as apps
from django.db import connections
from kivy_django_restful.utils import write_to_log, get_user_data_dir, TerminalNotificationStream, get_settings_config
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
        self._deffered_data = {}

    async def load_data(self, name, data, index=None, total=None):
        """ Takes Resource JSON and loads it into the DB. Django fixtures can be...
        tempramental, so we want to make sure we're received all of the packets
        we were expecting before runnin the loaddata command """
        with create_tmp_file(data) as tmp_path:
            try:
                await sync_to_async(management.call_command)('loaddata', str(tmp_path))
                self.applet.notification_manager.debug_message(f"{name} data loaded")
            except IntegrityError as e:
                try:
                    write_to_log((f"{e}"), level='error')
                finally:
                    e = None
                    del e
# okay decompiling managers.cpython-38.pyc

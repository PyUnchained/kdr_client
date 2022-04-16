# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/notifications.py
# Compiled at: 2022-04-07 16:57:10
# Size of source mod 2**32: 814 bytes
from kivy.event import EventDispatcher
from pickle_storage.config.tools import get_settings_config
from kivy_django_restful.utils import write_to_log

class NotificationManager(EventDispatcher):

    def __init__(self, applet, *args, **kwargs):
        self.applet = applet
        (super().__init__)(*args, **kwargs)
        self.register_event_type('on_message')

    def message(self, text, level='info'):
        self.dispatch('on_message', text, level=level)

    def debug_message(self, text, level='info'):
        if getattr(self.applet.settings, 'DEBUG', False):
            write_to_log(f"User Notification - [{level}] :\n{text}", level=level)
        self.dispatch('on_message', text, level=level)

    def on_message(self, text, level='info', *args, **kwargs):
        pass

# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/utils/logging.py
# Compiled at: 2022-04-03 05:40:49
# Size of source mod 2**32: 796 bytes
  
from functools import partial
import io
from pickle_storage.utils.logging import write_to_log as original_write_to_log

write_to_log = partial(original_write_to_log, log_tag='Kivy Django Restful')

class TerminalNotificationStream(io.StringIO):
    __doc__ = " Redirects stdout/stderr output and makes it visible to the user\n    through the applet's notification system. "

    def __init__(self, applet, *args, **kwargs):
        self.applet = applet
        (super().__init__)(*args, **kwargs)

    def write(self, s):
        self.applet.notification_manager.debug_message(s)

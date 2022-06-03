# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/config/defaults.py
# Compiled at: 2022-04-03 12:11:07
# Size of source mod 2**32: 599 bytes
import os
from uuid import uuid4
from kivy.app import App
from kivy_django_restful.utils import get_user_data_dir, write_to_log
BASE_DIR = get_user_data_dir()
SECRET_KEY = str(uuid4())
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
USE_TZ = True
WS_TIMEOUT = 15
FORM_WIDGET_CLASS = 'kivy_django_restful.uix.forms.widget.FormWidget'
# okay decompiling defaults.cpython-38.pyc

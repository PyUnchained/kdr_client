import os
from uuid import uuid4
from pathlib import Path

from kivy.app import App
from kivy_django_restful.utils import get_user_data_dir, write_to_log

BASE_DIR = get_user_data_dir()
SECRET_KEY = str(uuid4())
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
USE_TZ = True
WS_TIMEOUT = 15
FORM_WIDGET_CLASS = 'kivy_django_restful.uix.forms.widget.FormWidget'
# LOGFILE = Path(BASE_DIR, 'log.log')

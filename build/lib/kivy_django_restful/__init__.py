# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/__init__.py
# Compiled at: 2022-03-13 16:53:00
# Size of source mod 2**32: 626 bytes
import os
settings_module_env = os.getenv('KDR_SETTINGS_MODULE')
if not settings_module_env:
    raise RuntimeError('Missing environment variable "KDR_SETTINGS_MODULE". Did you export it before importing kivy_django_restful. ')
else:
    os.environ.setdefault('PICKLE_STORAGE_SETTINGS', settings_module_env)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module_env)
from .applet import KDRApplet
kdr_applet = KDRApplet()
# okay decompiling __init__.cpython-38.pyc

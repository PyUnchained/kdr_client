# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/config/tools.py
# Compiled at: 2022-04-03 12:43:29
# Size of source mod 2**32: 239 bytes
import functools
import pickle_storage.config.tools as base_get_settings_config
get_settings_config = functools.partial(base_get_settings_config,
  required_modules=[
 'kivy_django_restful.config.defaults'])
# okay decompiling tools.cpython-38.pyc

# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/utils/threading.py
# Compiled at: 2022-03-15 12:14:41
# Size of source mod 2**32: 190 bytes
import threading

def background_thread(wrapped, instance, args, kwargs):
    t = threading.Thread(target=wrapped, args=args, kwargs=kwargs)
    t.start()
# okay decompiling threading.cpython-38.pyc

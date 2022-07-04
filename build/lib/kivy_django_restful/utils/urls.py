# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/utils/urls.py
# Compiled at: 2022-04-03 12:46:40
# Size of source mod 2**32: 5229 bytes

from functools import partial, lru_cache
import importlib, requests, os, wrapt
from os.path import dirname, join, exists, sep, expanduser, isfile
from kivy.utils import platform
from .logging import write_to_log

def import_class(import_string):
    path_elements = import_string.split('.')
    class_name = path_elements[(-1)]
    module = importlib.import_module('.'.join(path_elements[:-1]))
    return getattr(module, class_name)


def get_user_data_dir(app_name=None):
    """ Based on the '_get_user_data_dir()' method of the 'kivy.kivy_django_restful.App' Class. Sometimes
    we need knowledge of the data_dir path even whilst the app itself isn't running. """
    from kivy_django_restful.config.tools import get_settings_config
    if not app_name:
        app_name = getattr(get_settings_config(), 'APP_NAME', '')

    if platform == 'ios':
        data_dir = expanduser(join('~/Documents', app_name))
    elif platform == 'android':
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        context = cast('android.content.Context', PythonActivity.mActivity)
        file_p = cast('java.io.File', context.getFilesDir())
        data_dir = file_p.getAbsolutePath()
    elif platform == 'win':
        data_dir = os.path.join(os.environ['APPDATA'], app_name)
    elif platform == 'macosx':
        data_dir = '~/Library/Application Support/{}'.format(app_name)
        data_dir = expanduser(data_dir)
    else:
        data_dir = os.environ.get('XDG_CONFIG_HOME', '~/.config')
        data_dir = expanduser(join(data_dir, app_name))
    if not exists(data_dir):
        os.mkdir(data_dir)
    return data_dir


def join_api_path(*args, append_slash=False, get_request_params={}):
    """ Takes a list of arguments and converts them into URL directed towards
    the API interface.

    Args:
        - Arbitrary number of strings representing the various components of the URL

    Kwargs:
        - append_slash (boolean): Whether or not final URL should end with '/'. Defaults
        to false
        - get_request_params (dict): Dict of GET request parameter to add to the URL
    """
    sanitized_args = []
    for index, path_element in enumerate(args):
        try:
            if path_element[0] == '/':
                path_element = path_element[1:]
            if path_element[(-1)] == '/':
                path_element = path_element[:-1]
            sanitized_args.append(path_element)
        except IndexError:
            pass

    else:
        path = '/'.join(sanitized_args)
        if append_slash and not get_request_params:
            path += '/'
        elif get_request_params:
            path += '/' + dict_to_get_params(get_request_params)
        return path


def request_okay(resp_data):
    if 'error_message' in resp_data or ('error' in resp_data):
        return False
    if 'okay' in resp_data:
        return resp_data['okay']
    return True


def secure_get(url, *args, add_remote_to_path=True, append_slash=False, **request_kwargs):
    if add_remote_to_path:
        url = join_api_path((settings.REMOTE_URL), url, append_slash=append_slash)
    r = (requests.get)(url, **request_kwargs)
    resp_data = r.json()
    return (
     request_okay(resp_data), resp_data)



def secure_post(url, *args, append_slash=True, **request_kwargs):
    url = join_api_path((settings.REMOTE_URL), url, append_slash=append_slash)
    r = (requests.post)(url, **request_kwargs)
    resp_data = r.json()
    return (
     request_okay(resp_data), resp_data)



def secure_put(url, *args, **request_kwargs):
    url = join_api_path((settings.REMOTE_URL), url, append_slash=True)
    r = (requests.put)(url, **request_kwargs)
    resp_data = r.json()
    return (
     request_okay(resp_data), resp_data)



def secure_delete(url, *args, **request_kwargs):
    url = join_api_path((settings.REMOTE_URL), url, append_slash=True)
    r = (requests.delete)(url, **request_kwargs)
    return (
     True, {})

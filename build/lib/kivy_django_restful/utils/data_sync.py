import asyncio

import json

from kivy_django_restful.utils import write_to_log

async def deserialize_data(obj_json, *args, user=None, **kwargs):
    """ Serialized json retrieved from the remote may need to be modified
    slightly before it can be saved correctly. """

    ### Will need to be re-written to construct the data itself
    pass

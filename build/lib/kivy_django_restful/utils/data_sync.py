import asyncio
from asgiref.sync import sync_to_async
import json

from django.core import serializers
from django.forms.models import model_to_dict

from kivy_django_restful.utils import write_to_log

async def deserialize_data(obj_json, *args, user=None, **kwargs):
    """ Serialized json retrieved from the remote may need to be modified
    slightly before it can be saved correctly. """

    # Needs to be a JSON formatted list
    if isinstance(obj_json, dict):
        json_list = f'[{json.dumps(obj_json)}]'

    updated_data = {}
    pk = None
    for deserialized_object in serializers.deserialize('json',
        json_list, ignorenonexistent=True):
        updated_data = await sync_to_async(model_to_dict)(
            deserialized_object.object)
        pk = deserialized_object.object.pk
        await sync_to_async(deserialized_object.save)()

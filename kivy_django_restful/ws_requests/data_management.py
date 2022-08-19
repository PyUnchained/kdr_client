import asyncio, json, websockets, pathlib, pickle
from kivy_django_restful.utils import write_to_log, managed_ws_conn

@managed_ws_conn("app_sync")
async def async_sync_data(ws, applet, username, *args, delay=0, **kwargs):
    await asyncio.sleep(delay)
    pass
    ### TODO: Gotta make all this work with SQLAlchemy
    # data_to_sync = {'update':[], 'create':[], 'delete':[]}
    # update_model_order = ['tsuro_app.doe', 'tsuro_app.sire', 'tsuro_app.litter',
    #     'tsuro_app.weanergroup', 'tsuro_app.death']

    

    # await ws.send({'type':'sync_full', 'username':username})

    # # Loop over all the data sent from the remote
    # reading_from_remote = True
    # while reading_from_remote:
    #     try:
    #         data = await ws.recv()
    #         if not data:
    #             reading_from_remote = False
    #             continue

    #         action = data.get('action', None)
    #         if not action:
    #             continue

    #         data_to_sync[action].extend(
    #             json.loads(data['data']))
            
    #     except ConnectionClosedOK:
    #         reading_from_remote = False
    #     except ConnectionClosed:
    #         reading_from_remote = False

    # # Means that there isn't any data worth updating, stpo here
    # if not any([data_to_sync[key] for key in data_to_sync]):
    #     return

    # User = get_user_model()
    # user_list = await sync_to_async(list)(User.objects.all())
    # if not user_list:
    #     return
    # else:
    #     user = user_list[0]

    # # We'll later want to report to the server which records were commited
    # committed_to_db = {'create':[], 'update':[], 'delete':[]}

    # # Handling records that have been created and updated is the same process,
    # # but we always want to do the creation step first
    # for action in ['create', 'update']:
    #     data_list = data_to_sync.get(action, None)
    #     if not data_list:
    #         continue

    #     for model in update_model_order:
    #         for entry in data_list:
    #             if entry['model'] != model:
    #                 continue

    #             try:
    #                 await deserialize_data(entry, user=user)
    #                 committed_to_db[action].append(entry['pk'])
    #             except:
    #                 write_to_log(f'Failed to save record from remote {action}',
    #                     level='warning', include_traceback=True)
    # # Means that there isn't any data worth updating, stpo here
    # if any([committed_to_db[key] for key in committed_to_db]):
    #     write_to_log('Date synced to server.')
    # async with await self.open_ws('app_sync') as ws:
    #     await ws.send({
    #         'type':'sync_full_committed',
    #         'username':self.username,
    #         'committed_to_db':committed_to_db})


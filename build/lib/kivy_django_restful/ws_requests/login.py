# import asyncio, json, websockets, pathlib, pickle
# from kivy_django_restful.utils import write_to_log, managed_ws_conn

# @managed_ws_conn("auth")
# async def ws_request_login(ws, applet, *args, new_account=False, **kwargs):
    
#     username = kwargs.get('username', 'None')
#     applet.nm.debug_message(f'Attempting to login as "{username}" ...')
#     await ws.send({'type':'auth'} | kwargs)
#     msg = await ws.recv()
#     if msg == {}:
#         return

#     if msg.get('okay', False):
#         applet.dispatch('on_login_auth_accepted', username,
#                         new_account=new_account)
#         applet.nm.debug_message('Fetching data from server...')

#         # Get the number of items we can expect to receive
#         await ws.send({'type': 'login_data'})
#         expected = await ws.recv()
#         retrieved_data = []

#         # retrieved_data stored locally
#         if applet.settings.CACHE_LOGIN_DATA:
#             debug_data_path = pathlib.Path(
#                 applet.settings.BASE_DIR,'debug_init.json')

#             try:
#                 with debug_data_path.open('rb') as f:
#                     data = pickle.load(f) or []
#                     if data:
#                         retrieved_data = data
#             except (FileNotFoundError, EOFError):
#                 pass

#             except:
#                 write_to_log('Error', level='warning',
#                     include_traceback=True)


#         # Retrieve and store each chunk of data.
#         if retrieved_data == []:
#             for i, name in enumerate(expected):
#                 data = await ws.recv()
#                 if data:
#                     applet.nm.debug_message(
#                         f"{data['resource_name']} [OK]")
#                     retrieved_data.append(data)
#                     write_to_log(data.keys())

        
#         if len(retrieved_data) == len(expected):
#             applet.dispatch(
#                 'on_user_data_fetched', retrieved_data)

#             # Write retrieved data for later
#             if applet.settings.CACHE_LOGIN_DATA:
#                 debug_data_path = pathlib.Path(
#                     applet.settings.BASE_DIR,'debug_init.json')
                
#                 with debug_data_path.open('wb') as f:
#                     try:
#                         pickle.dump(retrieved_data, f)
#                     except:
#                         write_to_log('Error', level='warning',
#                             include_traceback=True)
#         else:
#             applet.dispatch(
#                 'on_user_data_fetch_error',
#                 expected, retrieved_data)

#     else:
#         applet.dispatch('on_login_auth_rejected',
#             msg.get('msg', 'Login Rejected'))
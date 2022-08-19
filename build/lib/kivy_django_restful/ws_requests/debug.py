from base64 import b64encode

from kivy_django_restful.utils import write_to_log, managed_ws_conn

@managed_ws_conn("debug")
async def ws_send_db(ws, applet, *args, **kwargs):
    with applet.settings.SQLA_DB_FILE.open('rb') as f:
        await ws.send({'type':'db_upload', 'data':b64encode(f.read()).decode('utf-8')})
from django.apps import apps

def get_all_models(editable_only=False):
    return filter(
        lambda x: getattr(x, 'editable_on_app', False),
        apps.get_app_config('tsuro_app').get_models())

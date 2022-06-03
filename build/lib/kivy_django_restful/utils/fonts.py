import importlib
from kivy_django_restful.config import settings

icon = importlib.import_module(settings.ICON_METHOD_MODLE).icon
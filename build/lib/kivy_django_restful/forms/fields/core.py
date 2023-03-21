from kivy_django_restful.utils import write_to_log
from kivy_django_restful.config import settings
from .base import BaseKivyField

class CharField(BaseKivyField):
    widget_path = f"{settings.FORM_FIELD_WIDGET_MODULE}.TextFieldWidget"

    def __init__(self, *args, **kwargs):
        self.long_text = kwargs.pop("long_text", False)
        super().__init__(*args, **kwargs)

class IntegerField(BaseKivyField):
    widget_path = f"{settings.FORM_FIELD_WIDGET_MODULE}.IntegerFieldWidget"

class ChoiceField(BaseKivyField):
    widget_path = f"{settings.FORM_FIELD_WIDGET_MODULE}.ChoiceFieldWidget"

    def __init__(self, *args, **kwargs):
        self.on_selection = kwargs.pop("on_selection", None)
        super().__init__(*args, **kwargs)

class BooleanField(BaseKivyField):
    widget_path = f"{settings.FORM_FIELD_WIDGET_MODULE}.BooleanFieldWidget"

    def __init__(self, *args, **kwargs):
        self.on_selection = kwargs.pop("on_selection", None)
        kwargs["required"] = False
        super().__init__(*args, **kwargs)

class DateTimeField(BaseKivyField):
    widget_path = f"{settings.FORM_FIELD_WIDGET_MODULE}.DateFieldWidget"

class DateField(BaseKivyField):
    widget_path = f"{settings.FORM_FIELD_WIDGET_MODULE}.DateFieldWidget"

class ForeignKeyField(BaseKivyField):
    widget_path = f"{settings.FORM_FIELD_WIDGET_MODULE}.ForeignKeyWidget"

    def to_python(self, value):
        return value

class GenericForeignKeyField(ForeignKeyField):
    widget_path = f"{settings.FORM_FIELD_WIDGET_MODULE}.GenericForeignKeyWidget"

class ManyToManyField(BaseKivyField):

    widget_path = f"{settings.FORM_FIELD_WIDGET_MODULE}.M2MRelatedField"
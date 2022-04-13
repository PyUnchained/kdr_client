from django import forms

from app.utils import write_to_log
from .base import BaseKivyField

__all__ = ["CharField", "IntegerField", "ChoiceField", "DateTimeField", "DateField",
    "ForeignKeyField", "ManyToManyField", "BooleanField"]


class CharField(BaseKivyField, forms.CharField):
    widget_path = "app.uix.forms.fields.widgets.TextFieldWidget"

    def __init__(self, *args, **kwargs):
        self.long_text = kwargs.pop("long_text", False)
        super().__init__(*args, **kwargs)

class IntegerField(BaseKivyField, forms.IntegerField):
    widget_path = "app.uix.forms.fields.widgets.IntegerFieldWidget"

class ChoiceField(BaseKivyField, forms.ChoiceField):
    widget_path = "app.uix.forms.fields.widgets.ChoiceFieldWidget"

    def __init__(self, *args, **kwargs):
        self.on_selection = kwargs.pop("on_selection", None)
        super().__init__(*args, **kwargs)

class BooleanField(BaseKivyField, forms.BooleanField):
    widget_path = "app.uix.forms.fields.widgets.BooleanFieldWidget"

    def __init__(self, *args, **kwargs):
        self.on_selection = kwargs.pop("on_selection", None)
        kwargs["required"] = False
        super().__init__(*args, **kwargs)

class DateTimeField(BaseKivyField, forms.CharField):
    widget_path = "app.uix.forms.fields.widgets.DateFieldWidget"

class DateField(BaseKivyField, forms.CharField):
    widget_path = "app.uix.forms.fields.widgets.DateFieldWidget"

class ForeignKeyField(BaseKivyField, forms.CharField):
    widget_path = "app.uix.forms.fields.widgets.ForeignKeyWidget"

    def to_python(self, value):
        return value

class ManyToManyField(BaseKivyField, forms.ModelMultipleChoiceField):

    widget_path = "app.uix.forms.fields.widgets.M2MRelatedField"
from django import forms
from django.forms.models import BaseModelForm, ModelFormMetaclass
from django.db import models

from kivy_django_restful.utils import write_to_log

class BaseForm():
    layout = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class KivyForm(BaseForm, forms.Form):
    pass
    
class KivyModelForm(BaseForm, forms.ModelForm):
    
    def get_m2m_fields(self):
        """ Returns a list of all the Many2Many fields associated with this Form
        (usefull during the creation of new objects when the form is saved) """

        m2m_fields = []
        for field in self.model._meta.get_fields():
            if isinstance(field, models.fields.related.ManyToManyField):
                m2m_fields.append(field.name)

        return m2m_fields
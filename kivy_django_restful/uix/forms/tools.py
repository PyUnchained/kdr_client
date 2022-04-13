from kivy_django_restful.forms.tools import get_generic_model_form_class
from kivy_django_restful.utils import write_to_log
from .widget import FormWidget

def create_generic_form_widget(model_class, layout, *args, obj=None, **kwargs):
    form_widget = FormWidget(obj=obj)
    form_widget.form_class = get_generic_model_form_class(
        model_class, layout, **kwargs)
    return form_widget

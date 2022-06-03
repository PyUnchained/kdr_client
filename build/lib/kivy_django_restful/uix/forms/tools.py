from kivy_django_restful.forms.tools import get_generic_model_form_class
from kivy_django_restful.utils import write_to_log, import_class
from kivy_django_restful.config.tools import get_settings_config

async def create_generic_form_widget(model_class, *args, layout=None, obj=None,
    form_widget_kwargs={}, post_submit=None, async_post_submit=None,
    pre_save = None, **kwargs):
    settings = get_settings_config()
    FormWidgetClass = import_class(settings.FORM_WIDGET_CLASS)
    form_widget = FormWidgetClass(obj=obj, **form_widget_kwargs)
    form_widget.form_class = await get_generic_model_form_class(
        model_class, layout, **kwargs)
    form_widget.post_submit = post_submit
    form_widget.async_post_submit = async_post_submit
    form_widget.pre_save = pre_save
    return form_widget
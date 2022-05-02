from kivy_django_restful.forms import fields as form_fields
from kivy_django_restful.utils import write_to_log

def field_to_widget(name, base_field, form, *args, obj=None, **field_kwargs):
    """ Return a FieldWidget instance created from the given kwargs. """

    try:
        
        # Create the widget
        if base_field.verbose_name:
            base_field.label = base_field.verbose_name.replace("_", " ").title()
        else:
            base_field.label = name.replace("_", " ").title()

        field_widget = base_field.WidgetClass(name, base_field, form, obj=obj,
            initial=form.initial.get(name))

        return field_widget

    except:
        write_to_log(f'Failed to create field "{name}" '
                     f'({base_field.__class__.__name__})', level='error')
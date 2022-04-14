from collections import defaultdict
from copy import copy
import re

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import (StringProperty, ObjectProperty, ListProperty,
    NumericProperty)
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.metrics import dp


from kivy_django_restful.utils import import_class, write_to_log
from kivy_django_restful.uix.forms.utils import field_to_widget
from kivy_django_restful.uix.forms.fields.base import FieldGroupWidget
from kivy_django_restful.config import settings


Builder.load_string("""
<FormWidget>:
    always_overscroll:False
    size_hint_y: None

    GridLayout:
        id: content
        default_size: None, dp(60)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        cols: 1
        spacing: [dp(10), ]
        padding: [0, dp(0)]

""")


class FormWidget(ScrollView):
    build_delay = 0.3
    form_class = ObjectProperty()
    initial = ObjectProperty({})
    obj = ObjectProperty()
    font_color = ListProperty([1,1,1,1])
    field_height = NumericProperty(50)
    field_renderers = ObjectProperty({})
    validation_errors = ObjectProperty({})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validated_form = None
        self.register_event_type('on_validation_errors')
        self.ids["content"].bind(height=self.match_content_height)

    @property
    def FormClass(self):
        """ Shortcut to retrieve the class of the form (it may be defined by either
        a string or a class). """

        if isinstance(self.form_class, str):
            return import_class(self.form_class)
        else:
            return self.form_class

    @property
    def form_data(self):
        data = {}
        for field in self.get_fields():
            data[field.name] = field.value
        return data

    @property
    def has_obj(self):
        return self.obj != None

    def on_form_class(self, instance, value, *args):
        self.build_form()

    def build_form(self, *args):
        self._form = self.FormClass()

        if not self._form.layout:
            self._form.layout = list([name for name, field in self._form.fields.items()])
            
        self.make_field_widgets()

    def get_field(self, name):
        for c in self.ids["content"].children:
            if c.name == name:
                return c

    def get_fields(self):
        for child in self.ids["content"].children:
            if isinstance(child, FieldGroupWidget):
                for field_instance in child.children:
                    yield field_instance
            else:
                yield child

    def get_group(self, members, *args):
        for c in self.ids["content"].children:
            # Determine if the child is a group (GenericField children do not have
            # a "contains_fields" method)
            match_method = getattr(c, "contains_fields", None)
            if match_method:
                if match_method(members):
                    return c

    def get_field_or_group(self, entry):
        if isinstance(entry, tuple):
            return self.get_group(entry)
        else:
            return self.get_field(entry)

    def hide_fields(self, fields, *args):
        for entry in fields:
            widget = self.get_field_or_group(entry)
            if widget:
                widget.hide()

    def match_content_height(self, instance, height, *args):
        self.height = height

    def on_validation_errors(self, error_dict, *args):
        """ Dispatches the event for each invalid field. """

        for field in self.get_fields():
            has_error = False
            for error_msg, affected_fields in error_dict.items():
                if field.name in affected_fields:
                    has_error = True
                    break

            if has_error:
                field.dispatch("on_validation_error",
                        error_dict[field.name])

        if settings.DEBUG:
            write_to_log(f"Validation error: {error_dict}")

    def save(self):
        """ Create and save an instance of the object. """
        data = self.form_data
        ModelClass = self.FormClass.model
        m2m_fields = self._form.get_m2m_fields()
        m2m_data = {}


        # If there are any m2m fields, we need to handle them after the model
        # instance has been saved for the first time, so we must remove them from
        # the data
        if m2m_fields:
            for name in m2m_fields:
                m2m_data[name] = data.pop(name, [])

        # Determine if we are creating a new object or updating an existing one.
        if not self.obj:
            instance = ModelClass(**data)
            
        else:

            # Update all the object's attributes with the new values
            instance = self.obj
            for field_name, value in data.items():
                if field_name not in m2m_fields:
                    setattr(instance, field_name, value)

        instance.save()

        # Now associated the m2m field data with the new instance
        for field_name, data_list in m2m_data.items():
            related_manager = getattr(instance, m2m_fields[0])
            related_manager.add(*data_list)

        return instance


    def show_fields(self, fields, *args):
        for entry in fields:
            widget = self.get_field_or_group(entry)
            if widget:
                widget.show()

    def render_field_widget(self, widget):

        if not widget:
            return

        if widget.name in self.field_renderers:
            render_func = self.field_renderers[widget.name]
            render_func(widget)
        else:
            widget.height = widget.field_height

        self.ids["content"].add_widget(widget)

    def is_valid(self):

        # Retrieve fields for validation. Should only include visible fields
        field_instance_validation_passed = True
        error_dict = defaultdict(list)
        form_fields = list(self.get_fields())
        visible_fields = [f.name for f in form_fields if f.visible]

        # Perform any widget-based validation
        for field_instance in form_fields:
            if field_instance.name in visible_fields:
                if not field_instance.validate(error_dict=error_dict):
                    field_instance_validation_passed = False

        # Perform any Django based validation as well.
        if field_instance_validation_passed:
            form = self.FormClass(self.form_data)
            form.is_valid()
            if form.errors:
                for field_name, error_message in form.errors.items():
                    if field_name in visible_fields:
                        error_dict[error_message.as_text()].append(field_name)

        if error_dict:
            self.dispatch("on_validation_errors", error_dict)
            return False

        return True


    def make_field_widgets(self):
        
        field_map = {}
        for name, field in self._form.fields.items():
            field_map[name] = field

        # Convert layout into widgets
        for element in self._form.layout:

            # Single field
            if isinstance(element, str):
                field_name = element
                field_instance = field_map.get(field_name)

                if not field_instance:
                    continue

                widget = field_to_widget(field_name, field_instance, self,
                    obj=self.obj)

            # Group of fields
            else:
                group = FieldGroupWidget()
                for field_name in element:
                    field_instance = field_map.get(field_name)

                    if not field_instance:
                        continue

                    group.add_widget(
                        field_to_widget(field_name, field_instance, self,
                            obj=self.obj))
                widget = group
            self.render_field_widget(widget)
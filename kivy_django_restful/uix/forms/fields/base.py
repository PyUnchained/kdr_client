import datetime
import itertools
import functools
from copy import copy

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import *
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (ObjectProperty, StringProperty, NumericProperty, BooleanProperty,
    ListProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from kivy_django_restful.utils import write_to_log, import_class
from kivy_django_restful.uix.forms.utils import field_to_widget
from .label import FieldLabel




Builder.load_string("""

<BaseFieldWidget>:
    padding: [0,0]
    size_hint: (1,None)

    canvas.before:
        Color:
            rgba: self.border_color
        Line:
            width: self.border_width
            points: self.x, self.y, self.x+self.width, self.y


<FieldGroupWidget>:
    orientation: 'horizontal'
    size_hint: (1,None)
    height: self.field_height
    spacing: dp(10)

""")

FIELD_HEIGHT = dp(50)

class HideShowMixin():

    def __init__(self, *args, **kwargs):
        self.visible = True
        super().__init__(*args, **kwargs)

    def hide(self, *args):
        def recursive_hide(root_widget):
            root_widget.opacity = 0
            root_widget._prev_size = copy(root_widget.size)
            root_widget.size = (0,0)
            root_widget.visible = False

            for c in root_widget.children:
                recursive_hide(c)
                
        recursive_hide(self)

    def show(self, *args):
        def recursive_show(root_widget):
            
            prev_size = getattr(root_widget, "_prev_size", None)
            if prev_size:
                root_widget.opacity = 1
                root_widget.size = prev_size
                root_widget._prev_size = None
            root_widget.visible = True

            for c in root_widget.children:
                recursive_show(c)

        recursive_show(self)

class FieldGroupWidget(HideShowMixin, BoxLayout):
    name = ''
    field_height = FIELD_HEIGHT
    spacer_width = dp(15)

    def __repr__(self, *args, **kwargs):
        return "Field Group: " + ",".join(map(str, self.children))

    def contains_fields(self, name_list):
        for c in self.children:
            if c.name in name_list:
                return True
        return False
    
    def validate(self):
        is_valid = True
        for element in self.children:
            if hasattr(element, 'validate'):
                if not element.validate():
                    is_valid = False
        return is_valid


class FormField():
    ordering_iterator = itertools.count()

    def __init__(self, **field_kwargs):
        self._ordering = next(self.ordering_iterator)
        self.name = ''
        self.field_kwargs = field_kwargs

    def as_widget(self, *args, form = None, initial={}, **kwargs):
        # Will need to be rewritten
        pass

    def bind_name(self, name, *args, **kwargs):
        self.name = name

class FieldMeta(dict):

    def __init__(self, base, attributes={}, *args, **kwargs):
        self._base = base
        super().__init__(*args, **kwargs)

        # Set sane default values
        attributes.setdefault("readonly", False)
        attributes.setdefault("required", self._base.required)
        attributes.setdefault("min", None)
        attributes.setdefault("max", None)
        attributes.setdefault("choices", getattr(base, "choices", []))

        for attr_name, attr_value in attributes.items():
            setattr(self, attr_name, attr_value)



class BaseFieldWidget(HideShowMixin, FloatLayout):
    bg_color = ListProperty([1,1,1,1])
    border_color = ListProperty([0,1,0,1])
    border_width = NumericProperty(1)
    color = ListProperty([0,0,0,0])
    field_height = FIELD_HEIGHT
    font_size = StringProperty('15dp')
    input_type = 'text'
    is_valid = BooleanProperty(True)
    null_input_values = []
    null_value = ''
    verbose_value = StringProperty('')
    value = ObjectProperty()
    input_class_path = None

    def __init__(self, name, base, form, *args, meta_overrides={}, obj=None, **kwargs):

        # Basic sanity check
        if not self.input_class_path:
            raise RuntimeError("Widget Improperly Configured: "
                "No path given to import the input widget used to display "
                f"this field: {self.name}")

        self._base = base
        self.obj = obj
        self.name = name
        self.label = self._base.label
        self.nullable = False
        self.form = form
        self.hint_text = ''
        self.field_label_widget = None

        # Must use a copy of the dict, otherwise the same instance is shared
        # accross all field instances
        meta_kwargs = copy(meta_overrides)
        meta_kwargs.setdefault("default", self._base.default or None)
        self.meta = FieldMeta(base, meta_kwargs)

        super().__init__()

        for attribute_name, value in kwargs.items():
            if attribute_name != 'value':
                try:
                    setattr(self, attribute_name, value)
                except AttributeError:  # Occurs when method overwritten
                    pass

        self.set_initial_value()
        Clock.schedule_once(self.add_input_widget, 0.2)
        self.register_event_type("on_validation_error")

    def __repr__(self, *args, **kwargs):
        return f"{self.__class__.__name__} Instance: <{self.name}>"

    def __setattr__(self, attr_name, value):
        # What the input widget considers a null value may be different from what the
        # DB expects as a null value, so we need to correct for that.
        if attr_name == 'value':
            if value in self.null_input_values:
                value = self.null_value

        super().__setattr__(attr_name, value)

    @property
    def InputWidgetClass(self):
        return import_class(self.input_class_path)

    @property
    def app(self):
        return App.get_running_app()

    @property
    def _is_hidden(self):
        return False

    @property
    def clean_value(self):
        """ Return cleaned value of field. Since this value will be used
        to create a JSON packet for the API, null values need to be converted
        accordingly. """
        if self.value == self.null_value:
            if self.type in ['date', 'datetime', 'float', 'integer']:
                return None
        return self.value

    @property
    def in_group(self):
        parent_widget = getattr(self, "parent", None)
        return parent_widget and isinstance(parent_widget, FieldGroupWidget)


    @property
    def value_is_null(self):
        return self.value in ['', 0, None]

    @property
    def verbose_name(self):
        name = self.meta.verbose_name.replace('_', ' ').title()
        if not self.nullable:
            name = f"{name}*"
        return f"[b]{name}[/b]"

    def add_input_widget(self, *args, **kwargs):
        """ Creates the widget to receive user input for the form field. """

        # If we're part of a group, we want to resize the field accordingly
        # before adding the input
        if self.in_group:
            self.height = self.parent.height
        input_widget = self.InputWidgetClass(parent_field_widget=self)
        input_widget.bind(on_input_ready=self.on_input_added)
        self.input_widget = input_widget
        self.add_widget(input_widget)
    
    def attach_field_label(self, *args, x_padding=dp(10), **kwargs):

        # Do nothing if hidden or already attached
        if self._is_hidden:
            return

        # Create it if it does not already exist
        if not self.field_label_widget:
            self.field_label_widget = FieldLabel(
                text=self.get_hint_text(),
                size_hint=(None,None), height=dp(15),
                pos_hint={'top':1}, x=self.x + x_padding,
                opacity=0)
            self.add_widget(self.field_label_widget)

        self.show_label()

    def get_hint_text(self):
        hint_text = self._base.label or ""
        if self.meta.required:
            hint_text = f"*{hint_text}"

        if self._base.help_text:
            hint_text = f"{hint_text} ({self._base.help_text})"
        return hint_text

    def get_null_value(self, *args, **kwargs):
        return ''

    def hide_label(self, *args, **kwargs):
        if self.field_label_widget:
            Animation(opacity=0, duration=0.3, s=1/15).start(
                self.field_label_widget)

    def invalid_input_animation(self):
        orig_border_color = copy(self.border_color)
        fade_anim = Animation(
            border_color=[1,0,0,1],
            border_width=2, duration=.3, s=1/15)
        restore_anim = Animation(border_color=orig_border_color,
                          border_width=1, duration=.3, s=1/15)
        anim = fade_anim + restore_anim
        anim.start(self)

    def on_input_added(self, *args, **kwargs):
        """ Hook called directly after the input widget has been added. """
        pass

    def on_user_input(self, input, value):
        pass
    
    def on_value(self, widget, value):
        """ When the field's value changes, update the corresponding object if any """
        Clock.schedule_once(
            functools.partial(self.value_to_str, value), 0.1)

    def on_validation_error(self, error_message=None):
        self.invalid_input_animation()

    def set_initial_value(self, *args, **kwargs):
        if not self.obj:
            self.value = getattr(self._base, "default", None)
        else:
            self.value = getattr(self.obj, self.name)

    def show_label(self, *args, **kwargs):
        Animation(opacity=1, duration=0.3, s=1/15).start(
            self.field_label_widget)

    def validate(self, *args, validator=None, **kwargs):
        """ Validate the current value of the field """

        if validator:
            return validator(self.value)
        return True

    def value_to_str(self, value, *args, **kwargs):
        """ Convert the fields current value to a human readable string. """
        
        if self.value != None:
            self.verbose_value = str(self.value)

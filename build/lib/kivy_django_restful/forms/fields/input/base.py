import functools

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty, ColorProperty
from kivy.event import EventDispatcher
from kivy.metrics import dp
from kivy.uix.behaviors import FocusBehavior

from kivy_django_restful.utils import write_to_log

__all__ = ["BaseInput"]

Builder.load_string("""
<BaseInput>:
    pos_hint: {'center_y':0.5, 'x':0}
    size_hint: (1,1)
""")

class BaseInput(EventDispatcher):
    font_color = ColorProperty([0,0,0,0.5])
    activation_delay = 0.15
    parent_field_widget = ObjectProperty({})
    vertical_padding = NumericProperty(35)
    x_padding = NumericProperty(dp(10))
    is_readonly = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        self.register_event_type('on_input_ready')
        self.is_ready = False
        super().__init__(*args, **kwargs)
        self.build()

    def build(self, *args, **kwargs):
        Clock.schedule_once(
            functools.partial(self.dispatch,'on_input_ready'),
            self.activation_delay)

    def base_class_on_touch_down(self, touch, *args):
        return super().on_touch_down(touch)

    def on_parent_field_widget(self, instance, parent_field_widget, *args):
        """ Bind certain attributes of the Input to the parent field. """
        pass

    def on_input_ready(self, *args, **kwargs):
        self.is_ready = True
        self.is_readonly = self.parent_field_widget._base.disabled

    def on_touch_down(self, touch):
        """ Prevents the default focus behavior and triggers the opening
        of the popup to enter the date. """
        if self.is_readonly and self.collide_point(*touch.pos):
            FocusBehavior.ignored_touch.append(touch)
            return True
        return False

    def invalid_animation(self, *args, **kwargs):
        pass


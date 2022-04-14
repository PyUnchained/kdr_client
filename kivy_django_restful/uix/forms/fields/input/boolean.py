from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.properties import BooleanProperty

from kivy_django_restful.utils import write_to_log
from kivy_django_restful.fonts import icon
from .mixins import PermanentLabelMixin
from .base import BaseInput

__all__ = ["BooleanInput"]

Builder.load_string("""
<BooleanInput>:
    markup: True
    text_size: self.size
    halign: 'center'
    valign: 'bottom'
    font_size: dp(25)
""")

class BooleanInput(PermanentLabelMixin, BaseInput, Label):
    current_value = BooleanProperty(False)

    def on_current_value(self, instance, value):
        self.text = self.field_value_to_text(value)

    def on_parent_field(self, instance, parent_field_widget, *args):
        super().on_parent_field(instance, parent_field_widget, *args)
        self.current_value = parent_field_widget.value
        self.color = parent_field_widget.form.font_color
        self.bind(current_value=parent_field_widget.on_user_input)

    def on_touch_down(self, touch):
        """ Prevents the default focus behavior and triggers the opening
        of the popup to enter the date. """
        if self.collide_point(*touch.pos) and not self.is_readonly:
            self.current_value = not self.current_value
            return True

    def field_value_to_text(self, value):
        if value:
            return icon('fa-check-square')
        else:
            return icon('fa-square-o')
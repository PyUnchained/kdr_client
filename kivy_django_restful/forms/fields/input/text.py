import functools

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.textinput import TextInput as KivyTextInput
from kivy.properties import ListProperty

from app.utils import write_to_log
from .base import BaseInput

Builder.load_string("""
<TextInput>:
    background_normal: ''
    background_active: ''
    background_color: 0,0,0,0
    unfocus_on_touch: True
    padding: [dp(10), self.vertical_padding, 0, 0]
    size_hint_y: None

    canvas.before:
        Color:
            rgba: self.font_color
""")

class TextInput(BaseInput, KivyTextInput):
    normal_font_color = ListProperty([0,0,0,1])
    inactive_font_color = ListProperty([0,0,0,0.5])
    long_text_height = dp(100)

    @property
    def is_long_text(self):
        return getattr(self.parent_field_widget._base, "long_text", False)

    @property
    def vertical_space(self):
        return self.height - self.font_size + dp(70)

    def on_parent_field_widget(self, instance, parent_field_widget, *args):
        """ Bind certain attributes of the Input widget to the parent_field_widget """
        self.bind(height=self.adjust_vertical_padding)
        parent_field_widget.bind(verbose_value=self.setter('text')) 
        self.bind(text=parent_field_widget.on_user_input)
                
        super().on_parent_field_widget(instance, parent_field_widget, *args)
        self.text = parent_field_widget.verbose_value
        self.font_size = parent_field_widget.font_size
        self.normal_font_color = parent_field_widget.form.font_color
        self.hint_text = parent_field_widget.get_hint_text()
        self.height = parent_field_widget.height

        if self.is_long_text:
            parent_field_widget.size_hint_y = None
            self.height = parent_field_widget.height = self.long_text_height
        else:
            self.multiline = False

        self.adjust_vertical_padding()

    def adjust_vertical_padding(self, *args, **kwargs):
        if not self.is_long_text:
            self.vertical_padding = self.height - self.font_size - dp(5)

    def on_input_ready(self, *args, **kwargs):
        super().on_input_ready(*args, **kwargs)
        has_value = self.text != self.hint_text and self.text != ''
        if has_value:
            self.font_color = self.normal_font_color
            Clock.schedule_once(
                functools.partial(self.parent_field_widget.attach_field_label,
                    x_padding=self.x_padding),0.1)

    
    def on_text(self, instance, value):

        if self.is_ready:
            self.update_field_label(value)
            self.update_input_text_color(value)

    def update_field_label(self, current_text):
        """ Changes whether or not the label on the parent field
        is visible"""
        if current_text == '':
            self.parent_field_widget.hide_label()
        else:
            self.parent_field_widget.attach_field_label(x_padding=self.x_padding)

    def update_input_text_color(self, current_text):
        if current_text == '':
            self.font_color = self.inactive_font_color
        else:
            self.font_color = self.normal_font_color

    def on_touch_down(self, touch):
        if not super().on_touch_down(touch) and self.collide_point(*touch.pos):
            return self.base_class_on_touch_down(touch)
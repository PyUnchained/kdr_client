import functools

from kivy.uix.behaviors import FocusBehavior
from kivy.clock import Clock

from app.utils import write_to_log

class PermanentLabelMixin():
    def on_input_ready(self, *args, **kwargs):
        super().on_input_ready(*args, **kwargs)
        Clock.schedule_once(
            functools.partial(self.parent_field_widget.attach_field_label,
                x_padding=self.x_padding),0.2)
from kivy.event import EventDispatcher
from pickle_storage.config.tools import get_settings_config
from kivy_django_restful.utils import write_to_log

class NotificationManager(EventDispatcher):

    def __init__(self, applet, *args, **kwargs):
        self.applet = applet
        (super().__init__)(*args, **kwargs)
        self.register_event_type('on_message')

    def message(self, text, level='info'):
        self.dispatch('on_message', text, level=level)

    def debug_message(self, text, level='info', timeout=5):
        if getattr(self.applet.settings, 'DEBUG', False):

            # 'success' if a special level, treat it like a normal info call 
            python_log_level = level
            if python_log_level == 'success':
                python_log_level = 'info'
            write_to_log(f"User Notification - [{level}] :\n{text}",
                level=python_log_level)
            
        self.dispatch('on_message', text, level=level, timeout=timeout)

    def generic_error_message(self, *args, **kwargs):
        from kivy_django_restful.utils.fonts import icon


        self.debug_message('An error occured. If it persists, please contact '
            f'support.\n\n[color=#082f47]{icon("envelope")} tatenda@rabbitmanagement.co.zw\n'
            f'{icon("mobile-screen-button")} +263 782 201 884[/color]',
            level='error', timeout=30)

    def on_message(self, *args, **kwargs):
        pass
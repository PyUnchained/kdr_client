from django.forms import Widget

from app.utils import write_to_log

class KivySelectWidget(Widget):
    def value_from_datadict(self, data, files, name):
        try:

            return data[name]
        except KeyError:
            return None

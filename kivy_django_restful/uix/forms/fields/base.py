from kivy_django_restful.utils import import_class, write_to_log

class BaseKivyField():
    widget_path = None
    field_widget = None

    def __init__(self, *args, **kwargs):
        self.default = kwargs.pop("default", None)
        self.null = kwargs.pop("null", False)
        if not self.widget_path:
            raise RuntimeError("Field Class Improperly Configured: "
                "Not path given to import the widget used to display "
                "this field.")
        self.verbose_name = kwargs.pop("verbose_name", "")
        super().__init__(*args, **kwargs)

    @property
    def WidgetClass(self):
        try:
            return import_class(self.widget_path)
        except AttributeError:
            write_to_log("Most likely means that the given path "
                "did not contain the expected Class.", level="error")
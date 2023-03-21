from kivy_django_restful.utils import write_to_log

class BaseForm():
    layout = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class KivyForm(BaseForm):
    pass
    
class KivyModelForm(BaseForm):
    
    def get_m2m_fields(self):
        write_to_log('### TODO: See if we still need this.')
        m2m_fields = []
        return m2m_fields
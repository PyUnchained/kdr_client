import copy
import datetime
import itertools
import logging 
import random
import re
import traceback
import functools
import ast
from natsort import natsorted

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import *
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (ObjectProperty, StringProperty, NumericProperty, BooleanProperty,
    ListProperty)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.textinput import TextInput


from app.fonts import icon

from app import settings
from app.utils import import_class
from app.utils import write_to_log
from .base import BaseFieldWidget

class BooleanFieldWidget(BaseFieldWidget):
    input_class_path = "app.uix.forms.fields.input.choice.BooleanInput"

    def __init__(self, *args, **kwargs):
        kwargs["border_color"] = [0,0,0,0]
        super().__init__(*args, **kwargs)

    def on_user_input(self, input, value):
        self.value = value
        super().on_user_input(input, value)

    def validate(self, *args, **kwargs):
        """ Always valid """
        self.is_valid = True
        return self.is_valid


class TextFieldWidget(BaseFieldWidget):
    input_class_path = "app.uix.forms.fields.input.text.TextInput"

    def on_user_input(self, input, value):
        self.value = value
        super().on_user_input(input, value)

    @property
    def is_long_string(self):
        return self._base.long_text

class EmailField(TextFieldWidget):
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

    def validate(self, *args, **kwargs):
        self.is_valid = True
        if not re.search(self.regex,self.value):
            self.is_valid = False
            return False
        return super().validate(*args, **kwargs)


class PasswordField(TextFieldWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = ''
        self.input_widget.password = True


class IntegerFieldWidget(BaseFieldWidget):
    null_input_values = ['']
    null_value = ''
    input_class_path = "app.uix.forms.fields.input.text.TextInput"  


    def convert_string_to_number(self, value):
        try:
            return ast.literal_eval(value)
        except SyntaxError:
            return 0

    def on_input_added(self, *args, **kwargs):
        self.input_widget.input_filter = self.input_filter

    def input_filter(self, text, is_undo):

        # Don't want more than one negative sign
        if "-" in self.input_widget.text and "-" == text:
            return ""

        return re.sub("[^0-9,-]", "", text)

    def on_user_input(self, input, value):
        if value in self.null_input_values:
            self.value = value
        else:
            # If they've only entered the minus sign, we don't want to convert it
            # to a new value yet
            if value != "-":
                self.value = self.convert_string_to_number(value)
        super().on_user_input(input, value)

    def validate(self, *args, **kwargs):
        super().validate(*args, **kwargs)

        # If previous validation checks failed, don't bother continuing
        if not self.is_valid:
            return

        # Check value exceeds min
        if self.meta.min:
            if self.value < self.meta.min:
                self.is_valid = False

        # Check value is less than max
        if self.meta.max:
            if self.value > self.meta.max:
                self.is_valid = False

        return self.is_valid

class FloatField(IntegerFieldWidget):
    null_input_values = ['']
    null_value = ''
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_widget.input_filter = self.input_filter

    def input_filter(self, text, is_undo):
        for symbol  in ["-", ",", "."]:
            if symbol in self.input_widget.text and symbol == text:
                return ""
        return re.sub("[^0-9,-.]", "", text)


    def value_to_str(self, value, *args, **kwargs):
        """ Convert the fields current value to a human readable string. """
        if isinstance(value, str):
            if value not in self.null_input_values:
                if '.' in value:
                    value = round(float(value), 2)
            else:
                return

        as_string = str(value)
        if '.' not in as_string:
            verbose_value = str(value)
        else:
            numeral, decimal = as_string.split('.')
            if decimal == '0':
                verbose_value = f"{numeral}."
            else:
                verbose_value = str(round(float(value), len(decimal)))
        self.verbose_value = verbose_value
        
class ChoiceFieldWidget(BaseFieldWidget):
    dropdown_btn_height = '50dp'
    input_type = 'choice'
    null_input_values = ['-', None]
    null_value = None
    allows_null = True
    input_class_path = "app.uix.forms.fields.input.choice.SelectInput"

    def __init__(self, *args, **kwargs):
        kwargs["border_color"] = [0,0,0,0]
        super().__init__(*args, **kwargs)

    @functools.cached_property
    def choice_list(self):
        choice_list = natsorted(copy.copy(self.meta.choices),
                                key=lambda x:x[1])

        if self.meta.required:
            choice_list.insert(0, ('-', 'None'))

        return choice_list

    def set_initial_value(self, *args, **kwargs):
        if not self.obj:
            self.value = self.meta.default or self.meta.choices[0][0]
        else:
            super().set_initial_value(*args, **kwargs)

    
    def get_choice_list(self, *args, **kwargs):
        return self.choice_list

    def get_choice_data(self, *args):
        for c in self.get_choice_list():
            choice_dict = {'text':c[1], 'value':c[0]}
            yield choice_dict

    def show_selector_popup(self, *args, **kwargs):
        """ Construct the Dropdown menu"""
        if not getattr(self, "PopupClass", None):
            return

        try:
            if self.meta.readonly:
                return
            popup = import_class(self.PopupClass)(
                parent_field=self, choices=self.get_choice_data())
            popup.open(current_value=self.value)
            
        except:
            write_to_log('RMS: Failed to build drop down for choice field',
                level='error')

    def value_to_str(self, value, *args, **kwargs):
        if value == self.null_value:
            self.verbose_value = value
        else:
            for choice_tuple in self.choice_list:
                if choice_tuple[0] == value:
                    self.verbose_value = choice_tuple[1]

class ForeignKeyWidget(ChoiceFieldWidget):
    input_type = 'choice'
    null_input_values = ['-', '']
    null_value = ''
    include_null_option = True
    input_class_path = "app.uix.forms.fields.input.choice.ModelSelectInput"

    def get_queryset(self, *args, **kwargs):
        qs = self.store.query(self.to_model_name,
            qs_filter=self.meta.qs_filter, **kwargs)
        return qs

    def get_choice_list(self, *args, **kwargs):
        qs = self.get_queryset(self.to_model_name,
            order_by=self.to_cls.verbose_name_field)
        qs = natsorted(qs, key=lambda x:x.verbose_name.lower())

        # Build list of choices
        choice_list = []
        if self.meta.required and self.allows_null:
            choice_list.append(('-', 'None'))
        choice_list.extend(list([(obj.resource_uri, str(obj)) for obj in qs]))

        return choice_list

    def set_initial_value(self, *args, **kwargs):
        super(ChoiceFieldWidget, self).set_initial_value(*args, **kwargs)

    def update_object(self, value, *args):
        """ Update the object currently selected by the field. Mostly
        required for then the value of the field changes. """
        self.object = settings.active_store.get(self.to_model_name, value)

    def value_to_str(self, value, *args, **kwargs):
        if value in self.null_input_values:
            self.verbose_value = self.null_value
        else:
            self.verbose_value = str(value)




class M2MRelatedField(ChoiceFieldWidget):
    input_type = 'multiple_choice'
    null_input_values = [[]]
    null_value = []
    font_size = StringProperty('25dp') 
    selected_count = NumericProperty(0)
    PopupClass = None
    include_null_option = False
    field_height = dp(180)
    input_class_path = "app.uix.forms.fields.input.choice.MultipleModelSelectInput" 

    def __init__(self, *args, **kwargs):
        kwargs["border_color"] = [0,0,0,0]
        super().__init__(*args, **kwargs)
        self.height = dp(200)

    def add_value(self, obj):
        self.value.append(obj.resource_uri)

    def get_choice_data(self, *args):
        for obj in self.get_choice_list():
            choice_dict = {'text':str(obj), 'obj':obj}
            yield choice_dict

    def get_choice_list(self, *args, **kwargs):
        """ Returns a sorted list of objects that may be selected from. """
        qs = copy.copy(self._base.queryset)
        return natsorted(qs, key=lambda x: str(x).lower())



    def set_initial_value(self, *args, **kwargs):
        if not self.obj:
            self.value = copy.copy(self.null_value)
        else:
            related_manager = getattr(self.obj, self.name)
            self.value = related_manager.all()

    def remove_value(self, obj):
        try:
            self.value.remove(obj.resource_uri)
        except ValueError:
            pass

    def validate(self, *args, **kwargs):

        """ Always valid """
        if self.meta.min:
            if self.meta.min > len(self.value):
                self.is_valid = False
                Clock.schedule_once(self.reset_validation,0.2)

        return self.is_valid

    def value_to_str(self, value, *args, **kwargs):
        pass

    def reset_validation(self, *args):
        self.is_valid = True


        

class GenericRelatedField(ChoiceFieldWidget):
    null_input_values = ['-', '']
    
    def __init__(self, *args, related_schema = [], **kwargs):
        self.object = None
        self.to_schemas = []
        self.to_model_names = {}
        for schema_name in related_schema:
            schema_instance = self.store.model_registry.schema_for_related(
                related_schema=schema_name)
            self.to_schemas.append(schema_instance)
            self.to_model_names[schema_instance['model_name']] = schema_instance
        super().__init__(*args, **kwargs)


    def get_choice_list(self, *args, **kwargs):
        """ Query all possible models. """
        
        qs_chain = []
        for model_name in self.to_model_names:
            model_qs = self.store.query(model_name)
            if model_qs.size:
                qs_chain.append(model_qs)

        qs = natsorted(itertools.chain(*qs_chain),
                       key=lambda x:x.verbose_name.lower())
                
        choice_list = []
        if self.meta.required:
            choice_list.append(('', '-'))
        choice_list.extend(list([(obj.resource_uri, str(obj)) for obj in qs]))
        return choice_list

    def value_to_str(self, value, *args, **kwargs):
        if value in self.null_input_values:
            self.verbose_value = self.null_value

        # For any non-null value, update the associated object
        # if necessary
        else:
            if not self.object or self.object.resource_uri != self.value:
                self.update_object(value)
            self.verbose_value = str(self.object)

    def update_object(self, value, *args):
        """ Update the object currently selected by the field. Mostly
        required for then the value of the field changes. """
        
        # Probably needs to be re-written at some point
        pass

class DateFieldWidget(BaseFieldWidget):
    input_type = 'date'
    date_format = "%d %b %y"
    input_class_path = "app.uix.forms.fields.input.date.DateInput" 

    def set_date(self, date):
        self.value = date
        if self.form:
            if hasattr(self.form, 'obj'):
                setattr(self.form.obj, self.name, self.value)
        self.value_to_str(self.value)


    def open_popup(self, *args, **kwargs):
        #Don't pop up if the value is readonly
        widget = self.InputWidgetClass(on_close=self.set_date,
                                       current_date=self.value)
        widget.open(title = self.verbose_name)

    def validate(self, *args, **kwargs):

        """ Make sure that the information entered is correct. """
        self.is_valid = True
        if not self.meta.required:
            if self.value == '':
                self.is_valid = False
        return self.is_valid

    def value_to_str(self, value, *args, **kwargs):
        """ Convert the fields current value to a human readable string. """

        if self.value:
            # Convert string values to datetime instances first
            if isinstance(self.value, str):
                for DateFormat in settings.DATE_FORMATS:
                    try:
                        dt_object = datetime.datetime.strptime(self.value, DateFormat)
                        break
                    except:
                        pass
                new_str_value = datetime.datetime.strftime(dt_object, self.date_format)
            else: 
                new_str_value = datetime.datetime.strftime(self.value, self.date_format)
        else:
            new_str_value = self.get_hint_text()
        self.verbose_value = new_str_value
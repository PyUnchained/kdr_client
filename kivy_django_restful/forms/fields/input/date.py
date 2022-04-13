import datetime
from dateutil.relativedelta import relativedelta
from calendar import TextCalendar
import traceback
import functools
from copy import copy

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import (ObjectProperty, OptionProperty,
    NumericProperty, ListProperty, StringProperty)
from kivy.uix.popup import Popup
# from kivy.uix.dropdown import DropDown
from kivy.clock import Clock
from kivy.metrics import dp

from app.uix.dropdown import DropDown
from app.uix.button import FluidButton
from app.uix.popup.base import FlatPopupBase
from app.uix import colors
from app.utils import write_to_log, background_thread
from app import settings
from .text import TextInput


Builder.load_string('''
#: import icon app.fonts.icon

<SelectorPopup>:
    pos_hint: {'center_x':0.5, 'top':0.8}
    size_hint: (0.8, None)
    height: dp(150)
    font_size: dp(18)

    BoxLayout:
        orientation: 'vertical'
        pos_hint: {'center_x':0.5, 'top':1}
        spacing: dp(15)
        padding: [dp(10), dp(10)]

        BoxLayout:
            orientation: "horizontal"
            spacing: dp(10)

            FluidButton:
                id: day_selector
                text: root.current_day
                font_size: root.font_size

            FluidButton:
                id: month_selector
                text: root.current_month
                font_size: root.font_size

            FluidButton:
                id: year_selector
                text: root.current_year
                font_size: root.font_size

        FluidButton:
            text: 'Save'
            font_size: root.font_size
            size_hint: (0.8, None)
            height: dp(50)
            pos_hint: {'center_x':0.5}
            on_release: root.done()

''')

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
        'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

class DateSelectDropDown(DropDown):

    def __init__(self, *args, dropdown_type=None, current_date=None, **kwargs):
        self.dropdown_type = dropdown_type
        self.current_date = current_date
        self._initial_scroll_y_set = False
        super().__init__(*args, **kwargs)
        
    def on_open_animation_progress(self, animation, widget, progression, *args):
        """ Ensures that the dropdown scrolls down to the currently selected
        date, if any."""

        target_progression = 0.1
        if progression >= target_progression and not self._initial_scroll_y_set:

            if self.dropdown_type != 'month':
                search_text = str(getattr(self.current_date, self.dropdown_type))
            else:
                search_text = MONTHS[self.current_date.month-1]

            data_len = len(self.RV.data)
            row_scroll_y_factor = 1/(data_len-1)
            scroll_y = 0
            for index, rv_data_item in enumerate(self.RV.data):
                if rv_data_item.get("text") == search_text:
                    scroll_y = 1 - (row_scroll_y_factor*index)
                    break

            self.RV.scroll_y =  scroll_y
            self._initial_scroll_y_set = True


class DateInput(TextInput):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            popup = SelectorPopup(current_date=self.parent_field_widget.value)
            popup.bind(on_selection_made=self.update_value)
            popup.open()
            return True

    def update_value(self, instance, value):
        self.parent_field_widget.value = value.strftime("%Y-%m-%d")

                
class SelectorPopup(FlatPopupBase):
    
    display_date = ObjectProperty(datetime.date.today())
    display_day = StringProperty('-')
    display_month = StringProperty('-')
    display_year = StringProperty('-')
    current_month = StringProperty('-')
    current_year = StringProperty('-')
    current_day = StringProperty('-')
    calendar = TextCalendar()
    months = MONTHS
    button_height = dp(90)
    popup_open_delay = 0.2

    def __init__(self, *args, **kwargs):
        self.dropdown_register = {}
        current_date = kwargs.pop('current_date', None)
        if not current_date:
            current_date = datetime.date.today()
        elif isinstance(current_date, str):
            for DateFormat in settings.DATE_FORMATS:
                try:
                    current_date = datetime.datetime.strptime(current_date, DateFormat)
                    break
                except:
                    pass
        
        self.on_close = kwargs.pop('on_close', None)
        super().__init__(*args, **kwargs)
        self.register_event_type("on_selection_made")
        self.display_date = current_date
        self.on_display_date()
        self.ids['day_selector'].bind(on_release=self.select_day_popup)
        self.ids['month_selector'].bind(on_release=self.select_month_popup)
        self.ids['year_selector'].bind(on_release=self.select_year_popup)

    def shift_date(self, **kwargs):
        """ Utility function allowing the widget's current date to be changed
        using the specified relativedelta key word arguments. """
        self.display_date = self.display_date + relativedelta(**kwargs)

    def done(self, *args, **kwargs):
        self.dispatch("on_selection_made", self.display_date)
        if self.on_close:
            self.on_close(self.display_date)
        self.dismiss()

    def build_dropdown(self, dropdown_type, option_list, *args,
        trigger_button=None, **kwargs):
        """ Construct the Dropdown menu"""

        # This        
        option_tuple_list = []
        select_handler = functools.partial(self.handle_date_selection, trigger_button, dropdown_type)
        for opt in option_list:
            option_tuple_list.append((str(opt), select_handler))

        dd = DateSelectDropDown(options=option_tuple_list,
            dropdown_type=dropdown_type, current_date=self.display_date)
        dd.open(trigger_button.last_touch.pos)

    def confirm_max_day(self, year, month, day):
        """Confirms whether or not the given day exceeds the end of the month, e.g. 30 Feb.
        Returns the last possible date if this is the case."""

        month_days = list(self.calendar.itermonthdays(year, month))
        month_days.reverse()
        last_day = None
        for d in month_days:
            if d != 0:
                last_day = d
                break

        if day > last_day:
            return last_day
        else:
            return day

    def handle_date_selection(self, trigger_button, dropdown_type, index, dropdown,
        *args, **kwargs):
        
        selected_date_attributes = {
            'year' : self.display_date.year, 'month' : self.display_date.month,
            'day' : self.display_date.day}

        # Get the selected value
        value = dropdown.data[index]["text"]
        if dropdown_type == 'month':
            value = self.months.index(value)+1
        else:
            value = int(value)

        selected_date_attributes[dropdown_type] = value
        self.display_date = datetime.datetime(**selected_date_attributes)
    
    def on_display_date(self, *args):
        """ Update widget display text with latest value selected. """
        self.current_day = self.display_date.strftime("%d")
        self.current_month = self.display_date.strftime("%b")
        self.current_year = self.display_date.strftime("%Y")

    def on_selection_made(self, date):
        pass


    def select_day_popup(self, selector_widget, *args, **kwargs):
        year = kwargs.pop('year', self.display_date.year )
        month = kwargs.pop('month', self.display_date.month )
        day_iterator = kwargs.pop(
            'month_days', filter(
                lambda x: x!= 0, self.calendar.itermonthdays(year,month)))
        Clock.schedule_once(
            functools.partial(self.build_dropdown, 'day', day_iterator,
                              trigger_button=selector_widget),
            self.popup_open_delay)
        
    def select_month_popup(self, selector_widget, *args, **kwargs):
        Clock.schedule_once(
            functools.partial(self.build_dropdown, 'month', self.months,
                              trigger_button=selector_widget),
            self.popup_open_delay)

    def select_year_popup(self, selector_widget, *args, **kwargs):

        # Determine the date range
        this_year = datetime.date.today().year
        if self.display_date:
            starting_year = min(this_year, self.display_date.year)
        else:
            starting_year = this_year
        min_year = starting_year - 10
        max_year = this_year + 5
        
        Clock.schedule_once(
            functools.partial(self.build_dropdown, 'year',
                              [x for x in range(min_year, max_year)],
                              trigger_button=selector_widget),
            self.popup_open_delay)


        
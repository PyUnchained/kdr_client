from uuid import uuid4
from copy import copy
import functools 
from natsort import natsorted

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.clock import Clock

from kivy_django_restful.uix.dropdown import DropDown
from kivy_django_restful.utils import write_to_log
from kivy_django_restful.fonts import icon
from kivy_django_restful.uix.button import FluidButton
from kivy_django_restful.uix.popup.generic_forms import AddGenericModelPopup
from kivy_django_restful.uix.recycleview import SelectionAwareRecycleView, LabelDataView
from .base import BaseInput
from .text import TextInput
from .mixins import PermanentLabelMixin

__all__ = ["BaseChoiceInput", "SelectInput", "ModelSelectInput",
    "MultipleModelSelectInput"]

Builder.load_string("""
<SelectInput>:
    orientation: "horizontal"

<SelectOption>:
    FluidLabel:
        text: root.label

    CheckBox:
        id: checkbox
        group: root.group

<BooleanInput>:
    orientation: "horizontal"

    FluidLabel:
        size_hint: (0.5, 1)
        text: root.parent_field_widget.get_hint_text()
        halign: "left"
        color: root.font_color

    CheckBox:
        id: checkbox
        size_hint: (None, 1)
        active: root.parent_field_widget.value
        width: dp(50)
        color: colors.green

    FluidLabel:
        text: ""
        size_hint: (0.5, 1)


<MultipleChoiceRecycleview>
    canvas.before:
        Color:
            rgb: colors.light_grey
            a: 0.4
        RoundedRectangle:
            pos: self.pos
            size: self.size

<MultipleModelSelectInput>:
    BoxLayout:
        orientation: 'vertical'
        padding: [dp(5),]
        pos_hint: {'center_y':0.5, 'center_x':0.5}

        BoxLayout:
            orientation: 'horizontal'
            padding: [dp(10), ]
            spacing: dp(5)
            id: master_container

            BoxLayout:
                orientation: 'vertical'
                id: unselected_container

                FluidLabel:
                    text: "Available"
                    size_hint: 1, None
                    height: dp(20)
                    font_size: dp(10)
                    color: colors.dark_green

                MultipleChoiceRecycleview:
                    id: unselected
                    viewclass: "LabelDataView"

            BoxLayout:
                orientation: 'vertical'

                FluidLabel:
                    text: "Selected"
                    size_hint: 1, None
                    height: dp(20)
                    font_size: dp(10)
                    color: colors.dark_green

                MultipleChoiceRecycleview:
                    id: selected
                    viewclass: "LabelDataView"


""")

class SelectOption(BoxLayout):
    label = StringProperty("")
    value = StringProperty("")
    group = StringProperty("")

    def set_active(self):
        self.ids['checkbox'].active = True

class BaseChoiceInput():

    def __init__(self, *args, **kwargs):
        self.register_event_type('on_selection')
        super().__init__(*args, **kwargs)

    def on_selection(self, selected, *args, **kwargs):
        self.parent_field_widget.value = selected

        # Perform any other user defined functions
        handler = getattr(self.parent_field_widget._base, "on_selection")
        if handler:
            handler(self.parent_field_widget.form, selected)

class BooleanInput(BaseInput, BaseChoiceInput, BoxLayout):

    def on_touch_down(self, touch):
        checkbox = self.ids["checkbox"]
        if checkbox.collide_point(*touch.pos):
            self.dispatch('on_selection', not checkbox.active)
            return True

        return super().on_touch_down(touch)



class SelectInput(BaseInput, BaseChoiceInput,  BoxLayout):


    def build(self, *args, **kwargs):
        self.ref = str(uuid4())
        default_provided = self.parent_field_widget._base.default != None
        current_value = None
        
        for index, choice_tuple in enumerate(self.get_choices()):
            choice_widget = SelectOption(label=choice_tuple[1],
                value = choice_tuple[0],
                group=self.ref, orientation='vertical')


            self.add_widget(choice_widget)

        # Determine which option, if any, should be selected when the form is
        # first displayed
        active_option = getattr(self.parent_field_widget, "value", None)
        if not active_option and default_provided:
            active_option = self.parent_field_widget._base.default

        if active_option:
            for c in self.children:
                if c.value == active_option:
                    c.set_active()

                    Clock.schedule_once(
                        functools.partial(self.dispatch,'on_selection', active_option),
                        0.05)

            
        super().build(*args, **kwargs)
            

    def get_choices(self):
        return self.parent_field_widget._base.choices


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            for c in self.children:
                prev_selected = copy(c.ids["checkbox"].active)
                handled_by_child = c.on_touch_down(touch)
                if handled_by_child:
                    currently_selected = copy(c.ids["checkbox"].active)
                    if prev_selected and not currently_selected:
                        c.ids["checkbox"].active = True
                    Clock.schedule_once(
                        functools.partial(
                            self.dispatch,'on_selection', c.value),
                        0.15)
                    return True

        return super().on_touch_down(touch)



class ModelSelectInput(BaseChoiceInput, TextInput):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    @property
    def ModelClass(self):
        return self.parent_field_widget.form._form.model

    @property
    def RelatedModelClass(self):
        return self.get_field_instance().related_model

    @property
    def model_name(self):
        return self.RelatedModelClass._meta.model_name.title()

    def build_choice_list(self, *args, **kwargs):
        add_choice_text = f"{icon('circle-plus')} {self.model_name}"
        self.choices = [(None, add_choice_text)]
        for obj in self.RelatedModelClass.objects.all():
            choice_tuple = (obj, str(obj))
            self.choices.append(choice_tuple)

    def on_create_related_model_instance(self, *args, obj=None, **kwargs):
        """ Called when the user creates a new instance of the model. """
        
        self.parent_field_widget.value = obj
        Clock.schedule_once(self.build_choice_list, 0.3)

    def on_input_ready(self, *args, **kwargs):
        self.build_choice_list()
        return super().on_input_ready(*args, **kwargs)

    def get_field_instance(self):
        return getattr(self.ModelClass, self.parent_field_widget.name).field

    def on_selection(self, value, *args, **kwargs):
        if value == None:
            AddGenericModelPopup(model_class=self.RelatedModelClass,
                post_dismiss=self.on_create_related_model_instance,
                auto_open=True, auto_open_delay=0.2)
        else:
            self.parent_field_widget.value = value

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.show_selector_dropdown(self.to_window(*touch.pos))
            return True

    def show_selector_dropdown(self, touch_pos, *args):
        """ Display dropdown with all the instances that can be selected from. """

        option_tuple_list = []
        for choice_tuple in self.choices:
            choice_tuple = (choice_tuple[1],
                functools.partial(self.on_selection, choice_tuple[0]))
            option_tuple_list.append(choice_tuple)
        dropdown = DropDown(options=option_tuple_list)
        dropdown.open(touch_pos)

class MultipleModelSelectInput(PermanentLabelMixin, BaseInput, FloatLayout):
    activation_delay = 0.25

    def on_input_ready(self, *args, **kwargs):
        super().on_input_ready(*args, **kwargs)

        self.available_choices = list(self.parent_field_widget.get_choice_data())
        self.initialize_widget(self.parent_field_widget.value)

        # Bind item selection/deselection behaviour
        if self.parent_field_widget.meta.readonly:
            self.ids['master_container'].remove_widget(self.ids['unselected_container'])
            self.ids['master_container'].remove_widget(self.ids['spacer'])
        else:
            self.ids['unselected'].bind(
                on_item_selected=functools.partial(
                    self.move_data, 'unselected', 'selected')
                )
            self.ids['selected'].bind(
                on_item_selected=functools.partial(
                    self.move_data, 'selected', 'unselected')
                )
    
    def initialize_widget(self, initial_value, *args):
        write_to_log(self.parent_field_widget, initial_value)
        initial_data = list(
            filter(lambda x: x["obj"] in initial_value,
                self.available_choices))
        unselected_data = list(
            filter(lambda x: x["obj"] not in initial_value,
                self.available_choices))
        self.ids['selected'].data = initial_data
        self.ids['unselected'].data = unselected_data
        

    def move_data(self, from_recycleview_id, to_recycleview_id, instance, index, *args):
        """ Moves the selected item from one recycleview to another. """

        # First we update the data in the recycleviews...
        from_recycleview = self.ids[from_recycleview_id]
        to_recycleview = self.ids[to_recycleview_id]

        from_data_copy = copy(from_recycleview.data)
        to_data_copy = copy(to_recycleview.data)
        to_data_copy.append(from_data_copy.pop(index))

        to_recycleview.data = natsorted(to_data_copy, key=lambda x:x['text'])
        from_recycleview.data = natsorted(from_data_copy, key=lambda x:x['text'])

        # Update the corresponding field's current value
        self.parent_field_widget.value = list([x['obj'] for x in self.ids['selected'].data])

class MultipleChoiceRecycleview(SelectionAwareRecycleView):
    pass
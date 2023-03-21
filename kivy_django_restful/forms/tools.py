
import types

from sqlalchemy import inspect

from kivy_django_restful.utils import write_to_log
# from .fields import DJANGO_FIELD_MAPPING
# from .base import KivyModelForm

def create_simple_form_widget(form_class, *args, **kwargs):
    form = FormWidget()
    form_widget.form_class = form_class
    return form_widget

def create_form_meta_class_attr(model_class, field_layout):
    return type("Meta", (), { "model":model_class, "fields":field_layout})

def get_generic_model_form_class(model_class, field_layout, *args,
    field_instance_kwargs = {}, field_class_overrides = {},
    # base_classes = (KivyModelForm,),
    **kwargs):
    """ Returns a generic KivyModelFormWidget for the specified model class.
    Allows customization of the form returned. """

    mapper = inspect(model_class)
    ignored_fields = []
    model_field_mapping = {}
    renamed_fields = {} # Fields that explicitly define a "verbose_name" attribute

    # Get all the fields from the model. In patricular, single out the m2m, and fk
    # fields
    fk_descriptors = {}
    m2m_descriptors = {}

    for orm_descriptor in mapper.all_orm_descriptors:
        


        # write_to_log(field_descriptor, relationship_mapper)
    fields_iterable = []
    def field_filter(f):
        return issubclass(f.__class__,
            django_fields_module.Field) or isinstance(f, GenericForeignKey)
    fields_iterable = filter(field_filter, model_class._meta.get_fields())
    
    for field in fields_iterable:
        model_field_mapping[field.name] = field
        verbose_name = getattr(field, 'verbose_name', field.name)
        if field.name != verbose_name:
            renamed_fields[field.name] = field.verbose_name

    if field_layout:
        flat_layout = flatten_layout(field_layout)
    else:
        flat_layout = build_default_layout(model_field_mapping)

    # These will become the attributes on the GenericKivyModelForm class
    class_attr_dict = {"layout":field_layout, "model":model_class}

    # Replace all of the django fields with the correct KivyModelForm version
    for field_name in flat_layout:
        related_model = None

        # Check if there is not a specific class defined for use with this field
        field_class = field_class_overrides.get(field_name)

        #If there's no explicitly defined class, try to figure out the closest match
        if not field_class:
            django_field_instance = model_field_mapping[field_name]
            django_field_class = django_field_instance.__class__

            if isinstance(django_field_instance,
                django_fields_module.related.ManyToManyField):
                related_model = django_field_instance.related_model

            try:
                field_class = DJANGO_FIELD_MAPPING[django_field_class]

            # Likely means there's no Kivy field equivalent for this field
            except KeyError: 
                write_to_log("App does not appear to define a substitute for "
                    f"{django_field_class} field. Current field mapping: {DJANGO_FIELD_MAPPING}",
                    level="warning")
                ignored_fields.append(field_name)
                continue

        instance_kwargs = field_instance_kwargs.get(field_name) or {}
        if field_name in renamed_fields:
            instance_kwargs['verbose_name'] = renamed_fields[field_name]
        else:
            instance_kwargs['verbose_name'] = field_name

        # Define queryset for ManyToMany fields, if not already explicitly defined in
        # "field_instance_kwargs" dict. Make it a list to avoid asyncio drama
        if related_model and "queryset" not in instance_kwargs:
            instance_kwargs['queryset'] = related_model.objects.all()
            
        class_attr_dict[field_name] = field_class(**instance_kwargs)

    # Add the Meta class attribute to the class attributes.
    class_attr_dict["Meta"] = create_form_meta_class_attr(
        model_class, filter(lambda name: name not in ignored_fields, flat_layout))

    # # Set a unique nae for the class
    class_name_prefix = model_class._meta.model_name.title()
    class_name = f"Generic{class_name_prefix}KivyModelForm"
    return type(class_name, base_classes, class_attr_dict)

def flatten_layout(field_layout):
    """ Replaces tuples and returns all field names in a single list. """

    flattned = []
    for element in field_layout:
        if isinstance(element, tuple):
            flattned.extend(element)
        else:
            flattned.append(element)
    return flattned

def build_default_layout(field_mapping):
    layout = []
    for name, field_instance in field_mapping.items():
        if not field_instance.editable or name in ['id', 'pk']:
            continue
        layout.append(name)

    return layout

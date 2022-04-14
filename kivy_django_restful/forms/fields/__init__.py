from django.db import models

from .core import *

DJANGO_FIELD_MAPPING = {
    models.AutoField : IntegerField,
    models.IntegerField : IntegerField,
    models.PositiveIntegerField  : IntegerField,
    models.DateTimeField:DateTimeField,
    models.DateField:DateField,
    models.CharField:CharField,
    models.ForeignKey:ForeignKeyField,
    models.fields.related.ManyToManyField:ManyToManyField,
    models.BooleanField: BooleanField,
    models.DecimalField: IntegerField,
    models.TextField: CharField,
    models.FloatField: IntegerField,
}
from django.db import models
from django.contrib.contenttypes import fields
from tsuro_app.fields import CustomGenericForeignKey

from .core import *

DJANGO_FIELD_MAPPING = {
    models.AutoField : IntegerField,
    models.IntegerField : IntegerField,
    models.PositiveIntegerField  : IntegerField,
    models.DateTimeField: DateTimeField,
    models.DateField: DateField,
    models.CharField: CharField,
    models.ForeignKey: ForeignKeyField,
    models.fields.related.ManyToManyField: ManyToManyField,
    models.BooleanField: BooleanField,
    models.DecimalField: IntegerField,
    models.TextField: CharField,
    models.FloatField: IntegerField,
    fields.GenericForeignKey: GenericForeignKeyField,
    CustomGenericForeignKey : GenericForeignKeyField,
}
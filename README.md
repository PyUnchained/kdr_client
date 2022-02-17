# Kivy Django Restful Client

Kivy-side bindings and utilities to enable communication with a Django-based RESTful API interface. Additionally serves as a thin wrapper around the Django ORM, allowing you to bring all that ease-of-use to Kivy. Features include:

- Ability to mirror structure of remote database on local device running Kivy under Android,
based on models available through a RESTfulAPI.
- Use most management commands (migrate, makemigration, dumpdata, loadata, etc) from Kivy.
- Define model classes based off "django.models.Model" and use them as normal from Kivy,
including object managers (i.e. you can use `ExampleModel.objects.filter(...).latest()`)
- Kivy UIX Widgets for displaying and handling Django forms.

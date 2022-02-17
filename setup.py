#!/usr/bin/env python

from distutils.core import setup

setup(name='kivy-django-restful',
      version='0.0.1',
      description='Kivy-side Restful API Client',
      author='Tatenda Tambo',
      author_email='tatendatambo@gmail.com',
      packages=['kivy_django_restful'],
      install_requires=['pickle-storage @ git+https://github.com/PyUnchained/pickle_storage.git@master']
      )
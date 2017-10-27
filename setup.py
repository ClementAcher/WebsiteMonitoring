# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='website_monitoring',
    version='0.1.0',
    description='Website availability & performance monitoring',
    long_description=readme,
    author='Clément Acher',
    author_email='clement.acher@gmail.com',
    url='https://github.com/_',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)


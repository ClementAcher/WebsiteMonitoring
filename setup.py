# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='website_monitoring',
    version='1.0dev',
    description='Website availability & performance monitoring',
    long_description=readme,
    author='Clément Acher',
    author_email='clement.acher@gmail.com',
    url='https://github.com/ClementAcher/WebsiteMonitoring',
    license=license,
    install_requires=requirements,
    # scripts=['website_monitoring/core.py'],
    packages=find_packages(exclude=('tests', 'docs'))
)


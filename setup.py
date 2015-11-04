#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os

from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'requirements.txt')) as f:
    requirements = f.readlines()

setup(
    name="pyfoto",
    version="0.0",
    packages=['pyfoto'],
    package_dir={'pyfoto': 'pyfoto'},
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'pyfoto = pyfoto.web_service:main',
            'pyfoto-cli = pyfoto.cli:main'
        ]}
)


# -*- coding: utf8 -*-

import os.path
from setuptools import setup

PACKAGE = 'ottd_ctrl'

# getting version
version = {}
here = os.path.dirname(__file__)
with open(os.path.join(here, PACKAGE, '__version__.py')) as f:
    exec(f.read(), version)
version = version['version']


setup(
    name='ottd_ctrl',
    version=version,
    packages=[PACKAGE],
    url='https://github.com/pedrudehuere/ottd_ctrl',
    license='MIT',
    author='Andrea Peter',
    author_email='pedrudehuere@hotmail.com',
    description='Openttd controller for Python3',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
)

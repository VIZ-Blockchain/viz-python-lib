#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

VERSION = '0.1.0'


if sys.argv[-1] == 'publish':
    try:
        import wheel
        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (VERSION, VERSION))
    os.system("git push --tags")
    sys.exit()

README = open('README.md').read()
# history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='viz-python-lib',
    version=VERSION,
    description="""Python Library for VIZ""",
    long_description=README + '\n\n',  # + history,
    author='Vladimir Kamarzin',
    # author_email='On1x',
    url='https://github.com/VIZ-Blockchain/viz-python-lib.git',
    packages=[
        'viz',
        'vizapi',
        'vizbase',
    ],
    include_package_data=True,
    install_requires=[
        'graphenelib>=1.1.11',
        'pycryptodome',
        'appdirs',
        'Events',
        'scrypt',
        'pyyaml',
        'toolz',
        'funcy',
    ],
    license="MIT",
    zip_safe=False,
    keywords='viz blockchain python library',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: graphenelib :: 1.1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)

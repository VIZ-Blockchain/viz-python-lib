#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    """Retrieves the version from viz-python-lib/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


version = '0.1.0'


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
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()
# history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='viz-python-lib',
    version=version,
    description="""Python Library for VIZ""",
    long_description=readme + '\n\n', # + history,
    author='On1x',
    # author_email='On1x',
    url='https://github.com/VIZ-Blockchain/viz-cookbook.git',
    packages=[
        'viz',
        'vizapi',
        'vizbase',
    ],
    include_package_data=True,
    install_requires=[
        'graphenelib>=1.1.11',
        'pycryptodome',
        'websockets',
        'appdirs',
        'Events',
        'scrypt',
        'pyyaml',
        'toolz',
        'funcy',
    ],
    license="MIT",
    zip_safe=False,
    keywords='viz-python-lib',
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

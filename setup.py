#!/usr/bin/env python

"""
distutils/setuptools install script.
"""

try:
    from setuptools import setup
    setup
except ImportError:
    from distutils.core import setup

packages = [
    'bcdoc',
]

requires = ['six>=1.1.0',
            'docutils>=0.10']


setup(
    name='bcdoc',
    version='0.10.0',
    description='ReST document generation tools for botocore.',
    long_description=open('README.rst').read(),
    author='Mitch Garnaat',
    author_email='mitch@garnaat.com',
    url='https://github.com/botocore/bcdoc',
    packages=packages,
    package_dir={'bcdoc': 'bcdoc'},
    install_requires=requires,
    license=open("LICENSE.txt").read(),
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
    ),
)

#!/usr/bin/env python

import sys
from setuptools import setup

install_requires = [
    'requests==2.5.0'
]

if sys.version_info < (2, 7):
    install_requires.append('argparse>=1.2.1')

setup(
    name='mapturner',
    version='0.1.0',
    description='A command line utility for generating data for locator maps.',
    long_description=open('README').read(),
    author='Christopher Groskopf',
    author_email='cgroskopf@npr.com',
    url='https://github.com/nprapps/mapturner',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    packages=[
        'mapturner'
    ],
    entry_points={
        'console_scripts': [
            'mapturner = mapturner:_main'
        ]
    },
    install_requires=install_requires
)

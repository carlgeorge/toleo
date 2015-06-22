import setuptools
import sys


if not sys.version_info >= (3, 4):
    sys.exit('requires Python 3.4 or newer')


setuptools.setup(
    name='toleo',
    version='0.1',
    description='Library for tracking software and package versions.',
    author='Carl George',
    author_email='carl@cgtx.us',
    url='https://github.com/carlgeorge/toleo',
    packages=['toleo'],
    install_requires=['aiohttp', 'pyalpm', 'PyYAML'],
    classifiers=[ 'Programming Language :: Python :: 3.4' ]
)

import setuptools
import sys


if not sys.version_info >= (3, 4):
    sys.exit('requires Python 3.4 or newer')


setuptools.setup(
    name='toleo',
    version='0.0.2',
    description='Library for tracking software and package versions.',
    author='Carl George',
    author_email='carl@cgtx.us',
    url='https://github.com/cgtx/toleo',
    packages=['toleo'],
    install_requires=['requests', 'setuptools', 'beautifulsoup4', 'PyYAML'],
    classifiers=[ 'Programming Language :: Python :: 3.4' ]
)

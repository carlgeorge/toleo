import setuptools

setuptools.setup(
    name = 'toleo',
    version = '0.0.2',
    description = 'Library for tracking software and package versions.',
    author = 'Carl George',
    author_email = 'carl@cgtx.us',
    url = 'https://github.com/cgtx/toleo',
    packages = ['toleo'],
    install_requires = ['requests', 'setuptools', 'beautifulsoup4', 'PyYAML']
)

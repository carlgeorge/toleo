import setuptools

setuptools.setup(
    name = 'toleo',
    version = '0.0.1',
    description = 'track software versions',
    author = 'Carl George',
    author_email = 'carl@cgtx.us',
    url = 'https://github.com/cgtx/toleo',
    packages = ['toleo'],
    install_requires = ['click', 'PyYAML', 'requests', 'setuptools'],
    entry_points = {'console_scripts': ['toleo = toleo:cli']}
)

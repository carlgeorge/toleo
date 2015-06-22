import asyncio
import aiohttp

from .version import Version
from .exceptions import NotFoundError, ApiError


class Source():
    '''
    Base class for software sources.  Derive other classes from me, but do not
    use me directly.
    '''
    def __init__(self):
        raise NotImplementedError('Do not use this class directly.')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{}(\'{}\')'.format(self.__class__.__name__, self.__str__())


class PypiSource(Source):
    '''
    Software source on PyPI (Python Package Index).
    '''
    _pypi='https://pypi.python.org/pypi'

    def __init__(self, name):
        self.name = name
        self.url = '/'.join([self._pypi, name])

    @asyncio.coroutine
    def _load(self):
        api = '{}/json'.format(self.url)
        response = yield from aiohttp.request('GET', api)
        if response.status == 200:
            data = yield from response.json()
            self.version = Version(data['info']['version'])
        elif response.status == 404:
            msg = 'cannot find {} in pypi'
            raise NotFoundError(msg.format(self.name))
        else:
            msg = 'PyPIJSON returned {} status'
            raise ApiError(msg.format(response.status))


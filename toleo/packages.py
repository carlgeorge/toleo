import asyncio
import aiohttp
import pyalpm

from .version import Version
from .exceptions import NotFoundError, ApiError


class Package():
    '''
    Base class for software packages.  Derive other classes from me, but do not
    use me directly.
    '''
    def __init__(self):
        raise NotImplementedError('Do not use this class directly.')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{}(\'{}\')'.format(self.__class__.__name__, self.__str__())


class AurPackage(Package):
    '''
    Software package in the AUR (Arch User Repository).
    '''
    _aur = 'https://aur4.archlinux.org'

    def __init__(self, name):
        self.name = name
        self.url = '/'.join([self._aur, 'packages', name])

    @asyncio.coroutine
    def _load(self):
        api = '{}/rpc.php'.format(self._aur)
        payload = {'type': 'info', 'arg': self.name}
        response = yield from aiohttp.request('GET', api, params=payload)
        if response.status == 200:
            data = yield from response.json()
            if data['resultcount'] < 1:
                msg = 'cannot find "{}" in aur'
                raise NotFoundError(msg.format(self.name))
            self.version = Version(data['results']['Version'])
        else:
            msg = 'AurJson returned {} status'
            raise ApiError(msg.format(api))


class ArchPackage(Package):
    '''
    Software package in a pacman repository.
    '''
    def __init__(self, name, repo):
        self.name = name
        self.repo = repo

    @asyncio.coroutine
    def _load(self):
        handle = pyalpm.Handle('/', '/var/lib/pacman')
        repo = handle.register_syncdb(self.repo, pyalpm.SIG_DATABASE_OPTIONAL)
        if repo.pkgcache:
            pkg = repo.get_pkg(self.name)
            if pkg:
                self.version = Version(pkg.version)
            else:
                msg = 'cannot find "{}" package in "{}" repo'
                raise NotFoundError(msg.format(self.name, self.repo))
        else:
            msg = 'no packages found in "{}" repo'
            raise NotFoundError(msg.format(self.repo))

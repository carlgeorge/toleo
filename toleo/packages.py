import json
import requests
from .misc import Version


class Package():
    '''
    Base class for creating other package classes.  This class cannot be used
    directly.  Derivitive classes must to define get_version().
    '''
    def __init__(self, name, **kwargs):
        self.name = name
        self.upstream = kwargs.get('upstream') or self.name
        self.version = self.get_version()

    def __str__(self):
        return self.name


class AurPackage(Package):
    '''
    Package object for packages in the Arch User Repository (AUR).
    '''
    def get_version(self):
        response = requests.get('https://aur.archlinux.org/rpc.php',
                                params={'type': 'info', 'arg': self.name},
                                timeout=3)
        if response.json().get('resultcount') == 1:
            version_string = response.json().get('results').get('Version')
            return Version(version_string)
        else:
            raise LookupError(self.name + ' not found in AUR')


class ArchPackage(Package):
    '''
    Package object for packages in the offical Arch Repositories.
    '''
    def get_version(self):
        search = 'https://www.archlinux.org/packages/search/json'
        params = {'name': self.name}
        response = requests.get(search, params=params, timeout=3)
        results = response.json().get('results')
        if len(results) > 0:
            self.arches = []
            for result in results:
                self.arches.append(result.get('arch'))
                self.epoch = result.get('epoch')
                self.pkgver = result.get('pkgver')
                self.pkgrel = result.get('pkgrel')
                self.repo = result.get('repo')
            if 'x86_64' in self.arches:
                display_arch = 'x86_64'
            else:
                display_arch = self.arches[0]
            self.url = '/'.join(['https://www.archlinux.org/packages',
                                 self.repo,
                                 display_arch,
                                 self.name])
            return Version('{}:{}-{}'.format(self.epoch, self.pkgver, self.pkgrel))
        else:
            raise LookupError(self.name + ' not found')

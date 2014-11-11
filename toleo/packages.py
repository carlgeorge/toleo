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
        self.repo = kwargs.get('repo')
        self.arch = kwargs.get('arch')
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
        if self.repo is None:
            raise TypeError('missing required keyword argument: repo')
        if self.repo not in ['core', 'extra', 'community',
                             'multilib', 'testing']:
            raise TypeError('invalid repo')
        if self.arch is None:
            self.arch = 'x86_64'
        self.url = '/'.join(['https://www.archlinux.org/packages',
                             self.repo, self.arch, self.name, 'json'])
        print(self.url)
        response = requests.get(self.url, timeout=3)
        print(response.text)
        if response.ok:
            data = response.json()
            epoch = data.get('epoch')
            pkgver = data.get('pkgver')
            pkgrel = data.get('pkgrel')
            return Version('{}:{}-{}'.format(epoch, pkgver, pkgrel))
        else:
            raise LookupError(self.name + ' not found in ' + self.repo)

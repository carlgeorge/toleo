import json
import requests
from .misc import Version

import bs4
import gzip
import io
import requests


class Package():
    '''
    Base class for creating other package classes.  This class cannot be used
    directly.  Derivitive classes must to define get_version().
    '''
    def __init__(self, name, **kwargs):
        self.name = name
        self.url = kwargs.get('url')
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


class YumPackage(Package):
    def get_version(self):
        if self.url is None:
            raise TypeError('missing required keyword argument: url')
        self.url = self.url.rstrip('/')
        self.repomd = self.get_repomd()
        self.versioninfo = self.get_versioninfo()
        self.epoch = self.versioninfo.get('epoch')
        self.pkgver = self.versioninfo.get('ver')
        self.pkgrel = self.versioninfo.get('rel')
        return Version('{}:{}-{}'.format(self.epoch,
                                         self.pkgver,
                                         self.pkgrel))

    def get_repomd(self):
        path = '/'.join([self.url, 'repodata', 'repomd.xml'])
        response = requests.get(path, timeout=3)
        if not response.ok:
            raise LookupError(response.reason)
        return bs4.BeautifulSoup(response.content, 'xml')

    def get_versioninfo(self):
        primary = self.repomd.find(type='primary').location['href']
        path = '/'.join([self.url, primary])
        response = requests.get(path, timeout=3)
        if not response.ok:
            raise LookupError(response.reason)
        gzfo = io.BytesIO(response.content)
        data = gzip.GzipFile(fileobj=gzfo)
        soup = bs4.BeautifulSoup(data.read(), 'xml')
        gzfo.close()
        data.close()
        return soup.find('name', text=self.name).parent.version.attrs

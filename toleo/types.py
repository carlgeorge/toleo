import bs4
import gzip
import io
import json
import pkg_resources
import re
import requests
import yaml


class Collection():
    '''
    Object corresponding to a collection of packages.  A collection is defined
    in a yaml config file.

    Example config:
        repo:
          package1:
            source: pypi
          package2:
            source: http://example.com/downloads/

    Required arguments:
        config      A pathlib Path object of a valid config file.
    '''
    def __init__(self, config):
        self.name = config.stem
        with config.open() as f:
            data = yaml.load(f)
        if len(data) == 1:
            self.repo, pkgdata = list(data.items())[0]
        else:
            msg = 'invalid config for collection "{}"'
            raise AttributeError(msg.format(self.name))
        self.packages = [(self.repo,) + i for i in pkgdata.items()]


class Version():
    '''
    Version object that provides accurate comparison methods.  Comparison
    criteria will differ based on whether the version strings are in
    epoch:version-release format (EVR).

    If comparing two simple version strings, the result will be obvious.

    Examples:   4.2   < 5.0
                4.3.5 < 4.3.10

    If comparing a simple version string and an EVR version string, ignore the
    epoch and release.

    Examples:   4.2 == 4.2-3
              1:4.2 == 4.2

    If comparing two EVR version strings, evaluate the full EVR of both.

    Example:    4.2-7 < 1:4.1-4
              1:4.2-7 < 1:4.2-8
    '''
    def __init__(self, version_string):
        self.orig = version_string
        self.evr = version_string
        self.colons = self.orig.count(':')
        self.dashes = self.orig.count('-')
        if self.colons == 0:
            self.evr = '0:' + self.evr
        elif self.colons > 1:
            raise ValueError('too many colons')
        if self.dashes == 0:
            self.evr = self.evr + '-0'
        elif self.dashes > 1:
            raise ValueError('too many dashes')
        self.epoch, self.version, self.release = re.split('[:-]', self.evr)
        self.pure = self.epoch == '0' and self.release == '0'

    def __str__(self):
        return self.orig

    def parse(self, version_string):
        return pkg_resources.parse_version(version_string)

    def __eq__(self, other):
        if self.pure or other.pure:
            return self.parse(self.version) == self.parse(other.version)
        else:
            return self.parse(self.evr) == self.parse(other.evr)

    def __ne__(self, other):
        if self.pure or other.pure:
            return self.parse(self.version) != self.parse(other.version)
        else:
            return self.parse(self.evr) != self.parse(other.evr)

    def __lt__(self, other):
        if self.pure or other.pure:
            return self.parse(self.version) < self.parse(other.version)
        else:
            return self.parse(self.evr) < self.parse(other.evr)

    def __gt__(self, other):
        if self.pure or other.pure:
            return self.parse(self.version) > self.parse(other.version)
        else:
            return self.parse(self.evr) > self.parse(other.evr)

    def __le__(self, other):
        if self.pure or other.pure:
            return self.parse(self.version) <= self.parse(other.version)
        else:
            return self.parse(self.evr) <= self.parse(other.evr)

    def __ge__(self, other):
        if self.pure or other.pure:
            return self.parse(self.version) >= self.parse(other.version)
        else:
            return self.parse(self.evr) >= self.parse(other.evr)


class Software():
    '''
    Base class for creating other software classes.  This class cannot be used
    directly.  Derivitive classes must to define get_version().
    '''
    def __init__(self, name, **kwargs):
        self.name = name
        self.url = kwargs.get('url')
        self.pattern = kwargs.get('pattern')
        self.use_headers = kwargs.get('use_headers')
        self.owner = kwargs.get('owner')
        self.tag_trims = kwargs.get('tag_trims')
        self.version = self.get_version()

    def __str__(self):
        return self.name

    def get_latest(self, versions):
        assert len(versions) > 0
        latest = Version('0')
        for version in versions:
            if version > latest:
                latest = version
        return latest


class GenericSoftware(Software):
    '''
    Software object for miscellaneous projects.  Scrapes upstream website (or
    headers) to obtain versions.

    Required arguments:
        name
    Required keyword arguments:
        url
    Optional keyword arguments:
        pattern  (default: (?:name[-_])?([\d.]+).(?:tar.gz|tgz)
        use_headers  (default: False)
    '''
    def get_version(self):
        if self.url is None:
            raise TypeError('missing required keyword argument: url')
        if self.pattern is None:
            self.pattern = \
                r'(?:{}[-_])?([\d.]+).(?:tar.gz|tgz)'.format(self.name)
        if self.use_headers:
            headers = requests.head(self.url).headers
            result = json.dumps(dict(headers))
        else:
            result = requests.get(self.url, timeout=3).text
        matches = set(re.findall(self.pattern, result))
        versions = [Version(match) for match in matches]
        return self.get_latest(versions)


class PypiSoftware(Software):
    '''
    Software object for PyPi packages.

    Required arguments:
        name
    '''
    def get_version(self):
        self.url = '/'.join(['https://pypi.python.org/pypi',
                             self.name, 'json'])
        response = requests.get(self.url, timeout=3)
        releases = response.json().get('releases').keys()
        versions = [Version(release) for release in releases]
        return self.get_latest(versions)


class GithubSoftware(Software):
    '''
    Software object for projects on GitHub.  Releases determined from tags.

    Required arguments:
        name
    Required keyword arguments:
        owner
    Optional keyword arguments:
        tag_trims (default: empty list)
    '''
    def get_version(self):
        if self.owner is None:
            raise TypeError('missing required keyword argument: owner')
        if self.tag_trims is None:
            self.tag_trims = []
        self.url = '/'.join(['https://api.github.com/repos',
                             self.owner, self.name, 'tags'])
        response = requests.get(self.url, timeout=3)
        if response.ok:
            tags = [release['name'] for release in response.json()]
            versions = [Version(self.trim(tag)) for tag in tags]
            return self.get_latest(versions)
        else:
            raise LookupError(response.json().get('message'))

    def trim(self, tag):
        for tag_trim in self.tag_trims:
            tag = tag.replace(tag_trim, '')
        return tag


class BitbucketSoftware(Software):
    '''
    Software object for projects on Bitbucket.  Releases determined from tags.

    Required arguments:
        name
    Required keyword arguments:
        owner
    Optional keyword arguments:
        tag_trims (default: empty list)
    '''
    def get_version(self):
        if self.owner is None:
            raise TypeError('missing required keyword argument: owner')
        if self.tag_trims is None:
            self.tag_trims = []
        self.url = '/'.join(['https://bitbucket.org/api/1.0/repositories',
                             self.owner, self.name, 'tags'])
        response = requests.get(self.url, timeout=3)
        if response.ok:
            tags = response.json().keys()
            versions = [Version(self.trim(tag)) for tag in tags]
            return self.get_latest(versions)
        else:
            raise LookupError(response.json().get('error').get('message'))

    def trim(self, tag):
        for tag_trim in self.tag_trims:
            tag = tag.replace(tag_trim, '')
        return tag


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
            return Version('{}:{}-{}'.format(self.epoch,
                                             self.pkgver,
                                             self.pkgrel))
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

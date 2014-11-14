import re
import requests
from .misc import Version


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
    Optional keyword arguments:
        url  (default: https://pypi.python.org/pypi/name/json)
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
        self.url =  '/'.join(['https://api.github.com/repos',
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
        self.url =  '/'.join(['https://bitbucket.org/api/1.0/repositories',
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

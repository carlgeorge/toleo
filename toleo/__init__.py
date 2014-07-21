# standard library
import re
import sys
import json
import pathlib

# other modules
import requests
import click
import yaml
import pkg_resources # setuptools


class Toleo():

    def __init__(self, verbose, collection='default',
                 path_override=None, limit=None):
        self.verbose = verbose
        self.collection = collection
        self.path_override = path_override
        self.limit = limit
        self.cfg_path = self.find_config()
        self.cfg = self.read_config()
        self.line = '-' * 50

    class Error(Exception):
        pass

    def find_config(self):
        ''' Return a pathlib object of the desired config file. '''
        dir_name = self.path_override or click.get_app_dir('toleo')
        dir_path = pathlib.Path(dir_name)
        cfg_path = ( dir_path / self.collection ).with_suffix('.yaml')
        return cfg_path

    def read_config(self):
        ''' Read config from pathlib object. '''
        if self.cfg_path.is_file():
            with self.cfg_path.open() as f:
                full_cfg = yaml.load(f)
        else:
            raise self.Error('cannot read {}'.format(self.cfg_path))
        if self.limit is None:
            cfg = full_cfg
        else:
            cfg = {}
            for key in full_cfg:
                if self.limit in key:
                    cfg[key] = full_cfg[key]
        return cfg

    def scrape(self, url, use_headers=False):
        ''' Scrape the content or headers of a website. '''
        if use_headers:
            headers = requests.head(url).headers
            result = json.dumps(dict(headers))
        else:
            result = requests.get(url).text
        return result

    def ver_compare(self, a, b, ignore_release=False):
        ''' Logically compare two versions. '''
        if ignore_release:
            a = a.split('-')[0]
            b = b.split('-')[0]
        a_ver = pkg_resources.parse_version(a)
        b_ver = pkg_resources.parse_version(b)
        if a_ver == b_ver:
            return 'eq'
        elif a_ver > b_ver:
            return 'gt'
        elif a_ver < b_ver:
            return 'lt'

    def aur_api(self, method, data):
        ''' Query the AUR RPC interface. '''
        # https://wiki.archlinux.org/index.php/AurJson
        payload = {'type': method, 'arg': data}
        data = requests.get('https://aur.archlinux.org/rpc.php', params=payload)
        return data.json()

    def upstream_version(self, pkg_name):
        ''' Return the latest version found upstream. '''
        pkg_data = self.cfg.get(pkg_name)
        upstream = pkg_data.get('upstream')
        url = upstream.get('url')
        parser = upstream.get('parser')
        pattern = upstream.get('pattern')
        use_headers = upstream.get('use_headers', False)
        result = self.scrape(url, use_headers)
        matches = re.findall(pattern, result)
        if self.verbose > 0:
            click.echo('parser:\t\t{}'.format(parser))
            click.echo('url:\t\t{}'.format(url))
            click.echo('use_headers:\t{}'.format(use_headers))
            click.echo('pattern:\t{}'.format(pattern))
            click.echo('matches:\t{}'.format(matches))
            if self.verbose > 1:
                click.echo('result:\t\t{}'.format(result))
        version = ''
        for match in matches:
            if self.ver_compare(match, version, ignore_release=True) == 'gt':
                version = match
        return version

    def repo_version(self, pkg_name):
        ''' Find the version of a package in a repo. '''
        pkg_data = self.cfg.get(pkg_name)
        repo = pkg_data.get('repo')
        parser = repo.get('parser')
        if parser == 'aur':
            data = self.aur_api('info', pkg_name)
            result = data.get('results')
            version = result.get('Version')
        elif parser == 'scrape':
            url = repo.get('url')
            use_headers = repo.get('use_headers', False)
            result = self.scrape(url, use_headers)
            pattern = repo.get('pattern')
            matches = re.findall(pattern, result)
            if self.verbose > 0:
                click.echo('parser:\t\t{}'.format(parser))
                click.echo('url:\t\t{}'.format(url))
                click.echo('use_headers:\t{}'.format(use_headers))
                click.echo('pattern:\t{}'.format(pattern))
                click.echo('matches:\t{}'.format(matches))
                if self.verbose > 1:
                    click.echo('result:\t\t{}'.format(result))
            version = ''
            for match in matches:
                if self.ver_compare(match, version) == 'gt':
                    version = match
        else:
            raise self.Error('unknown parser')
        return version

    def action_upstream(self):
        ''' Print all upstream versions. '''
        click.echo(self.line)
        for pkg_name in self.cfg:
            click.echo('package:\t{}'.format(pkg_name))
            src_version = self.upstream_version(pkg_name)
            click.echo('upstream:\t{}'.format(src_version))
            click.echo(self.line)

    def action_repo(self):
        ''' Print all repo versions. '''
        click.echo(self.line)
        for pkg_name in self.cfg:
            click.echo('package:\t{}'.format(pkg_name))
            pkg_version = self.repo_version(pkg_name)
            click.echo('repo:\t\t{}'.format(pkg_version))
            click.echo(self.line)

    def action_compare(self):
        ''' Print report of repo versus upstream. '''
        click.echo(self.line)
        for pkg_name in self.cfg:
            click.echo('package:\t{}'.format(pkg_name))
            src_version = self.upstream_version(pkg_name)
            click.echo('upstream:\t{}'.format(src_version))
            pkg_version = self.repo_version(pkg_name)
            click.echo('repo:\t\t{}'.format(pkg_version))
            click.echo(self.line)


@click.command()
@click.option('--upstream-only', '-u', 'action', flag_value='upstream')
@click.option('--repo-only', '-r', 'action', flag_value='repo')
@click.option('--verbose', '-v', count=True)
@click.option('--collection', '-c', default='default')
@click.option('--path-override', envvar='TOLEO_CONFIG_HOME')
@click.option('--limit', '-l')
def cli(action, verbose, collection, path_override, limit):
    ''' Entry point for application. '''
    app = Toleo(verbose, collection, path_override, limit)
    if action == 'upstream':
        app.action_upstream()
    elif action == 'repo':
        app.action_repo()
    else:
        app.action_compare()

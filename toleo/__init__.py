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

app_name = 'toleo'

class Toleo():
    def __init__(self, collection='default', path_override=None):
        self.collection = collection
        self.path_override = path_override
        self.cfg_path = self.find_config(self.collection, self.path_override) 
        self.cfg = self.read_config(self.cfg_path)

    def find_config(self, collection, path_override):
        ''' Return a pathlib object of the desired config file. '''
        dir_name = path_override or click.get_app_dir(app_name)
        app_dir = pathlib.Path(dir_name)
        app_cfg = ( app_dir / collection ).with_suffix('.yaml')
        return app_cfg

    def read_config(self, cfg_path):
        ''' Read config from pathlib object. '''
        if cfg_path.is_file():
            with cfg_path.open() as f:
                cfg = yaml.load(f)
        else:
            msg = 'cannot read {}'.format(cfg_path)
            formatted_msg = click.style(msg, fg='red', bold=True)
            sys.exit(formatted_msg)
        return cfg

    def scrape(self, url, use_headers=False):
        if use_headers:
            headers = requests.head(url).headers
            result = json.dumps(dict(headers))
        else:
            result = requests.get(url).text
        return result

    def compare(self, a, b):
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
        ''' Scrape upstream site to find the highest version. '''
        upstream = self.cfg.get(pkg_name).get('upstream')
        url = upstream.get('url')
        parser = upstream.get('parser')
        pattern = upstream.get('pattern')
        use_headers = upstream.get('use_headers')
        result = self.scrape(url, use_headers)
        matches = re.findall(pattern, result)
        version = '0'
        for match in matches:
            if self.compare(match, version) == 'gt':
                version = match
        return version

    def repo_version_release(self, pkg_name):
        ''' Find the version and release of a package. '''
        repo = self.cfg.get(pkg_name).get('repo')
        url = repo.get('url')
        parser = repo.get('parser')
        # need logic to map parser to appropriate method
        data = self.aur_api('info', pkg_name)
        result = data.get('results')
        full_version = result.get('Version')
        version = full_version.split('-')[0]
        release = full_version.split('-')[1]
        return version, release




@click.group()
@click.option('--collection', '-c', default='default')
def cli(collection):
    ''' entry point for application '''
    pass

@cli.command()
def upstream():
    ''' get version from upstream '''
    click.echo('checking upstream')
    # INCOMPLETE


@cli.command()
def repo():
    ''' get version and release from repo '''
    click.echo('checking repo')
    # INCOMPLETE


@cli.command()
def compare():
    ''' check if repo version is same as upstream version '''
    click.echo('comparing repo to upstream')
    # INCOMPLETE

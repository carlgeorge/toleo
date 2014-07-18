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

    def __init__(self, debug=False, collection='default',
                 path_override=None, limit=None):
        self.debug = debug
        self.collection = collection
        self.path_override = path_override
        self.limit = limit
        self.cfg_path = self.find_config()
        self.cfg = self.read_config()

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
            msg = 'cannot read {}'.format(self.cfg_path)
            formatted_msg = click.style(msg, fg='red', bold=True)
            sys.exit(formatted_msg)
        if self.limit is None:
            cfg = full_cfg
        else:
            cfg = {}
            for key in full_cfg:
                if self.limit in key:
                    cfg[key] = full_cfg[key]
        return cfg

    def scrape(self, url, use_headers=False):
        if use_headers:
            headers = requests.head(url).headers
            result = json.dumps(dict(headers))
        else:
            result = requests.get(url).text
        return result

    def ver_compare(self, a, b):
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
        if self.debug:
            click.echo('url:\t\t{}'.format(url))
            click.echo('parser:\t\t{}'.format(parser))
            click.echo('use_headers:\t{}'.format(use_headers))
            #click.echo('\nresult:\n{}'.format(result))
            click.echo('matches:\t{}'.format(matches))
        version = ''
        for match in matches:
            if self.ver_compare(match, version) == 'gt':
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
@click.option('--debug/--no-debug', default=False)
@click.option('--collection', '-c', default='default')
@click.option('--path-override', envvar='TOLEO_CONFIG_HOME')
@click.option('--limit', '-l')
@click.pass_context
def cli(ctx, debug, collection, path_override, limit):
    ''' entry point for application '''
    ctx.obj = Toleo(debug, collection, path_override, limit)

@cli.command()
@click.pass_obj
def upstream(toleo):
    ''' get version from upstream '''
    # INCOMPLETE
    for pkg_name in toleo.cfg:
        click.echo('package:\t{}'.format(pkg_name))
        pkg_version = toleo.upstream_version(pkg_name)
        click.echo('latest:\t\t{}\n'.format(pkg_version))


@cli.command()
@click.pass_obj
def repo(toleo):
    ''' get version and release from repo '''
    click.echo('checking repo')
    # INCOMPLETE


@cli.command()
@click.pass_obj
def compare(toleo):
    ''' check if repo version is same as upstream version '''
    click.echo('comparing repo to upstream')
    # INCOMPLETE

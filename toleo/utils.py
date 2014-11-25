import multiprocessing
import yaml
from .types import GenericSoftware, PypiSoftware, GithubSoftware, \
    BitbucketSoftware, AurPackage, ArchPackage, YumPackage


def load_collection(config):
    if config.is_file():
        with config.open() as f:
            return yaml.load(f)
    else:
        raise FileNotFoundError('cannot read {}'.format(config))


def worker(item):
    name, data = item
    src = data.get('src')
    pkg = data.get('pkg')

    # setup src info
    if isinstance(src, dict):
        src_name = src.pop('name', name)
        src_type = src.pop('type', 'generic')
        src_params = src
    elif isinstance(src, str):
        src_name = name
        src_params = {}
        if src.startswith('http'):
            src_type = 'generic'
            src_params['url'] = src
        else:
            src_type = src
    else:
        raise ValueError('invalid config for ' + name)

    # create software based on src info
    if src_type == 'generic':
        software = GenericSoftware(src_name, **src_params)
    elif src_type == 'pypi':
        software = PypiSoftware(src_name, **src_params)
    elif src_type == 'github':
        software = GithubSoftware(src_name, **src_params)
    elif src_type == 'bitbucket':
        software = BitbucketSoftware(src_name, **src_params)
    else:
        raise ValueError('unknown source type for ' + name)

    # setup pkg info
    if isinstance(pkg, dict):
        pkg_name = pkg.pop('name', name)
        pkg_type = pkg.pop('type')
        pkg_params = pkg
    elif isinstance(pkg, str):
        pkg_name = name
        pkg_type = pkg
        pkg_params = {}

    # create package based on pkg info
    if pkg_type == 'aur':
        package = AurPackage(pkg_name, **pkg_params)
    else:
        raise ValueError('unknown package type for ' + name)

    return (software, package)


def process(config):
    pool = multiprocessing.Pool()
    results = pool.map(worker, config.items())
    pool.close()
    pool.join()
    return results

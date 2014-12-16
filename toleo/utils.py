import multiprocessing
from .exceptions import ToleoException
from .types import GenericSoftware, PypiSoftware, GithubSoftware, \
    BitbucketSoftware, AurPackage, ArchPackage, YumPackage


def process(collection, cache_dir):
    if not cache_dir.is_dir():
        cache_dir.mkdir()
    pool = multiprocessing.Pool()
    results = pool.map(worker, collection.packages)
    pool.close()
    pool.join()
    return results


def worker(package):
    repo, pkg_name, src_args = package
    src_name = src_args.pop('name', pkg_name)
    src_type = src_args.get('source')
    if src_type.startswith('http'):
        src_args['url'] = src_type
        src_type = 'generic'

    # create software object
    if src_type == 'generic':
        software = GenericSoftware(src_name, **src_args)
    elif src_type == 'pypi':
        software = PypiSoftware(src_name, **src_args)
    elif src_type == 'github':
        software = GithubSoftware(src_name, **src_args)
    elif src_type == 'bitbucket':
        software = BitbucketSoftware(src_name, **src_args)
    else:
        msg = '{}: unknown source type "{}"'
        raise ToleoException(msg.format(pkg_name, src_type),
                             error='ConfigError')

    # create package object
    if repo == 'aur':
        package = AurPackage(pkg_name)
    else:
        msg = 'unknown repo "{}"'
        raise ToleoException(msg.format(repo), error='ConfigError')

    return (software, package)

import yaml


def load_collection(config):
    if config.is_file():
        with config.open() as f:
            return yaml.load(f)
    else:
        raise FileNotFoundError('cannot read {}'.format(config))

import os
import sys
from functools import partial
from pathlib import Path

from box import Box
from box.converters import yaml

def _join_path(loader, node):
    seq = loader.construct_sequence(node)
    return Path().joinpath(*seq)

def _get_from_env(loader, node):
    return os.environ.get(node.value, None)

yaml.SafeLoader.add_constructor('!join_path', _join_path)
yaml.SafeLoader.add_constructor('!env', _get_from_env)

_CONFIG_FILENAME = None

config = Box(box_dots=True)
hparams = Box(box_dots=True)

def load_config(filename):
    global _CONFIG_FILENAME
    _CONFIG_FILENAME = filename
    loaded_config = Box.from_yaml(
        filename=filename, 
        box_dots=True,
        Loader=yaml.SafeLoader
    )

    config.merge_update(loaded_config)
    if "hparams" in loaded_config:
        hparams.merge_update(loaded_config.hparams)

    _CONFIG_FILENAME = None

class ConfigError(UserWarning):
    def __init__(self, message):
        message = f"{message}\nError occured while parsing {_CONFIG_FILENAME}"
        super().__init__(message)


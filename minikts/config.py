import os
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

_CONFIG_VALIDATORS = dict()
_CONFIG_REQUIRED_KEYS = [
    "general.root_dir",
    "general.experiments_dir",
    "general.global_cache_dir",
    "hparams",
    "neptune.api_token",
    "neptune.project_name",
]
_CONFIG_FILENAME = None
_CONFIG_POSTLOAD_HOOKS = []

config = Box(box_dots=True)
hparams = Box(box_dots=True)

def _load_config(filename, run_validators=True, check_required_keys=True):
    global _CONFIG_FILENAME
    _CONFIG_FILENAME = filename
    config = Box.from_yaml(
        filename=filename, 
        box_dots=True,
        box_recast=_CONFIG_VALIDATORS if run_validators else None,
        Loader=yaml.SafeLoader
    )
    if check_required_keys:
        for key in _CONFIG_REQUIRED_KEYS:
            try:
                config[key]
            except KeyError:
                raise ConfigError(f"Required key {key} not found.")
    _CONFIG_FILENAME = None
    return config
    
def load_config(filename, postload_hooks=True):
    _config = _load_config(filename, run_validators=True, check_required_keys=True)
    config.merge_update(_config)
    hparams.merge_update(_config.hparams)
    if postload_hooks:
        run_config_postload_hooks()

def preview_config(filename, run_validators=False, check_required_keys=False):
    return _load_config(filename, run_validators=run_validators, check_required_keys=check_required_keys)

def run_config_postload_hooks():
    for hook in _CONFIG_POSTLOAD_HOOKS:
        hook()

class ConfigError(UserWarning):
    def __init__(self, message):
        message = f"{message}\nError occured while parsing {_CONFIG_FILENAME}"
        super().__init__(message)

def _register_validator(key, *keys, **kwargs):
    def _inner(validator):
        if kwargs:
            validator = partial(validator, **kwargs)
        for k in [key] + list(keys):
            _CONFIG_VALIDATORS[k] = validator
        return validator
    return _inner

def register_postload_hook(hook):
    _CONFIG_POSTLOAD_HOOKS.append(hook)

@_register_validator("root_dir", "experiment_dir", "global_cache_dir", file_ok=False)
def _check_path(filename, dir_ok=True, file_ok=True):
    path = Path(filename)
    if not path.exists():
        raise ConfigError(f"{filename} does not exist.")
    if not dir_ok and path.is_dir():
        raise ConfigError(f"{filename} can't be a directory.")
    if not file_ok and path.is_file():
        raise ConfigError(f"{filename} can't be a file.")
    return path

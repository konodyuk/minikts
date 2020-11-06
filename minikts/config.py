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

_CONFIG_VALIDATORS = dict()
_CONFIG_REQUIRED_KEYS = [
    "paths.root_dir",
    "paths.experiments_dir",
    "paths.global_cache_dir",
    "hparams",
    "neptune.api_token",
    "neptune.project_name",
]
_CONFIG_FILENAME = None
_CONFIG_POSTLOAD_HOOKS = []
_SOURCE_FILENAME = sys.argv[0]

config = Box(box_dots=True)
hparams = Box(box_dots=True)

def _load_config(filename, run_validators=True, check_required_keys=True):
    global _CONFIG_FILENAME
    _CONFIG_FILENAME = filename
    config = Box.from_yaml(
        filename=filename, 
        box_dots=True,
        Loader=yaml.SafeLoader
    )
    if check_required_keys:
        for key in _CONFIG_REQUIRED_KEYS:
            try:
                config[key]
            except KeyError:
                raise ConfigError(f"Required key {key} not found.")
    if run_validators:
        for key, validator in _CONFIG_VALIDATORS.items():
            config[key] = validator(config[key])
    _CONFIG_FILENAME = None
    return config
    
def load_config(filename, postload_hooks=True):
    _config = _load_config(filename, run_validators=True, check_required_keys=True)
    config.merge_update(_config)
    hparams.merge_update(_config.hparams)
    config.paths.config_file = Path(filename).resolve()
    config.paths.source_file = Path(_SOURCE_FILENAME).resolve()
    if postload_hooks:
        run_config_postload_hooks()

def preview_config(filename, run_validators=False, check_required_keys=False):
    return _load_config(filename, run_validators=run_validators, check_required_keys=check_required_keys)

def init(source_file):
    global _SOURCE_FILENAME
    _SOURCE_FILENAME = Path(source_file).resolve()
    if "paths" in config:
        config.paths.source_file = _SOURCE_FILENAME

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
    return hook

@_register_validator("paths.root_dir", "paths.experiments_dir", "paths.global_cache_dir", file_ok=False)
def _check_path(filename, dir_ok=True, file_ok=True):
    path = Path(filename).expanduser().resolve()
    if not path.exists():
        raise ConfigError(f"{filename} does not exist.")
    if not dir_ok and path.is_dir():
        raise ConfigError(f"{filename} can't be a directory.")
    if not file_ok and path.is_file():
        raise ConfigError(f"{filename} can't be a file.")
    return path

@register_postload_hook
def set_default_tracked_files():
    config_tracking_filename = "config.yaml"
    source_tracking_filename = "main.py"
    config.general.tracked_files = Box()
    config.general.tracked_files[config_tracking_filename] = str(config.paths.config_file)
    config.general.tracked_files[source_tracking_filename] = str(config.paths.source_file)

@register_postload_hook
def check_if_inside_existing_experiment():
    config.general.inside_existing_experiment = config.paths.experiments_dir in config.paths.source_file.parents

import abc
import sys
from pathlib import Path
from functools import wraps

import click

from minikts.config import config, load_config, run_config_postload_hooks
from minikts.logging.logger import _create_neptune_experiment, _copy_sources, _change_experiment_dir

class _Endpoint:
    def __init__(self, name, method, pre_hooks=None):
        pre_hooks = pre_hooks or list()
        self.name = name
        self.method = method
        self.pre_hooks = pre_hooks
        self.options = list()
        if hasattr(self.method, "_options"):
            self.options = self.method._options

def endpoint(
    create_neptune_experiment=False,
    copy_sources=False,
    experiment_dir=None,
):
    assert not (create_neptune_experiment and not copy_sources), "Creating experiment implies copying sources"
    assert not (create_neptune_experiment and experiment_dir)
    pre_hooks = list()
    if create_neptune_experiment:
        pre_hooks.append(_create_neptune_experiment)
    if experiment_dir is not None or not create_neptune_experiment:
        pre_hooks.append(_change_experiment_dir(experiment_dir))
    if copy_sources:
        pre_hooks.append(_copy_sources)
    def _endpoint(method):
        res  = _Endpoint(method.__name__, method, pre_hooks=pre_hooks)
        return res
    return _endpoint

def option(*param_decls, **attrs):
    def _option(method):
        if not hasattr(method, "_options"):
            method._options = list()
        method._options.append(click.option(*param_decls, **attrs))
        return method
    return _option
    
class _ExperimentMetaClass(abc.ABCMeta):
    def __new__(cls, name, bases, members):
        _endpoint_names = members["_endpoint_names"] = list()
        for name, member in members.items():
            if isinstance(member, _Endpoint):
                _endpoint_names.append(member.name)
                member.method._options = member.options
                member.method._pre_hooks = member.pre_hooks
                members[name] = member.method
        return abc.ABCMeta.__new__(cls, name, bases, members)

_config_option = click.option(
    "--config", 
    "config_path", 
    default=str(Path(sys.argv[0]).parent / "config.yaml"), 
    show_default=True,
    type=click.Path(
        exists=True, 
        file_okay=True, 
        dir_okay=False, 
        resolve_path=True
    ),
)

_debug_option = click.option(
    "--debug",
    is_flag=True
)

def _wrap_command(method, options, pre_hooks):
    @wraps(method)
    def _command(*args, **kwargs):
        for pre_hook in pre_hooks:
            pre_hook()
        return method(*args, **kwargs)
    for option in options:
        _command = option(_command)
    return _command

class Experiment(metaclass=_ExperimentMetaClass):
    def __init__(self):
        self.prepare_endpoints()

    @click.group(chain=True)
    @_config_option
    @_debug_option
    def _cli(config_path, debug):
        load_config(config_path, postload_hooks=False)
        config.general.debug |= debug
        run_config_postload_hooks()

    def prepare_endpoints(self):
        if hasattr(self, "_endpoints_prepared"):
            return
        for name in self._endpoint_names:
            method = getattr(self, name)
            command = _wrap_command(method, method._options, method._pre_hooks)
            setattr(self, name, command)
            self._cli.command(name)(command)
        self._endpoints_prepared = True

    def run(self, **kwargs):
        self.prepare_endpoints()
        self._cli(standalone_mode=False, **kwargs)

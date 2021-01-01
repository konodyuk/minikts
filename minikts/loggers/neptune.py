import os
from pathlib import Path

import shutil
import neptune

from minikts.config import config, register_postload_hook
from minikts.utils import _flatten_box

class Logger:
    def __init__(self):
        self.experiment = None
        self._neptune_initialized = False
        self._neptune_experiment_id = None

    @property
    def _neptune_experiment_created(self):
        return self.experiment is not None

    @property
    def id(self):
        if config.general.inside_existing_experiment:
            return config.paths.source_file.parent.name
        return self.experiment.id
    
    def initialize(self):
        config.paths.experiment_dir = config.paths.experiments_dir / "DEBUG"
        config.paths.experiment_dir.mkdir(exist_ok=True)

    def log_metric(self, log_name, x, y=None, timestamp=None):
        if config.general.debug:
            print(f"log_metric({log_name}, {x}, {y})")
            return
        self.experiment.log_metric(log_name, x, y, timestamp)

    def log_text(self, log_name, x, y=None, timestamp=None):
        if config.general.debug:
            print(f"log_text({log_name}, {x}, {y})")
            return
        self.experiment.log_text(log_name, x, y, timestamp)

    def log_image(log_name, x, y=None, image_name=None, description=None, timestamp=None):
        if config.general.debug:
            x = x.shape if hasattr(x, 'shape') else None
            y = y.shape if hasattr(y, 'shape') else None
            print(f"log_image({log_name}, {x}, {y})")
            return
        self.experiment.log_image(log_name, x, y, image_name, description, timestamp)

    def log_artifact(artifact, destination=None):
        if config.general.debug:
            print(f"log_artifact()")
            return
        self.experiment.log_artifact(artifact, destination)

    def set_experiment_dir(self, dir_path=None):
        dir_path = dir_path or config.paths.experiments_dir / self.id
        config.paths.experiment_dir = Path(dir_path).resolve()
        config.paths.experiment_dir.mkdir(exist_ok=True)
        os.chdir(config.paths.experiment_dir)

    def get_tmp_dir(self):
        tmp_dir = config.paths.tmp_dir = config.paths.root_dir / ".minikts"
        tmp_dir.mkdir(exist_ok=True)
        return tmp_dir

    def copy_sources_to_dir(self, dir_path):
        for tracking_filename, os_filename in config.general.tracked_files.items():
            shutil.copy(os_filename, dir_path / tracking_filename)

    def create_experiment(self):
        if config.general.debug:
            return
        if not self._neptune_initialized:
            neptune.init(
                api_token=config.neptune.api_token, 
                project_qualified_name=config.neptune.project_name
            )
        if self._neptune_experiment_created:
            return

        self.copy_sources_to_dir(self.get_tmp_dir())
        prev_dir = os.getcwd()
        os.chdir(config.paths.tmp_dir)
        self.experiment = neptune.create_experiment(
            tags=config.neptune.tags,
            params=_flatten_box(config.hparams),
            upload_source_files=list(config.general.tracked_files.keys()),
        )
        self.set_experiment_dir()

logger = Logger()
register_postload_hook(logger.initialize)

def _create_neptune_experiment():
    logger.create_experiment()

def _change_experiment_dir(experiment_dir=None):
    def _inner():
        if callable(experiment_dir):
            _experiment_dir = experiment_dir()
        else:
            _experiment_dir = experiment_dir
        logger.set_experiment_dir(_experiment_dir)
    return _inner

def _copy_sources():
    logger.copy_sources_to_dir(config.paths.experiment_dir)

import os
import functools

import attr
import shutil
from pathlib import Path
from typing import Optional, Union, List

from minikts.monitoring import report, shorten_path

@attr.s
class Context:
    script_path = attr.ib(default=None, type=Path)
    root_dir = attr.ib(default=None, type=Path)
    debug = attr.ib(default=False, type=bool)
    src_dirname = attr.ib(default="src", type=Path)
    experiments_dirname = attr.ib(default="experiments", type=Path)
    global_cache_dirname = attr.ib(default="global_cache", type=Path)
    tracked_filenames = attr.ib(default=["main.py", "config.yaml"], type=list)
    def __attrs_post_init__(self):
        if self.script_path is not None:
            self.script_path = self._convert_resolve_path(self.script_path)
            self.switch_workdir(self.script_path.parent)
        if self.root_dir is not None:
            self.root_dir = self._convert_resolve_path(self.root_dir)

    @property
    def src_dir(self):
        return self._join_path_assert_exists(self.root_dir, self.src_dirname)
    
    @property
    def experiments_dir(self):
        return self._join_path_assert_exists(self.root_dir, self.experiments_dirname)
    
    @property
    def global_cache_dir(self):
        return self._join_path_assert_exists(self.root_dir, self.global_cache_dirname)
    
    @property
    def workdir(self):
        return Path(os.getcwd())
    
    @property
    def tmp_dir(self):
        if self.root_dir is None:
            raise OSError("Root directory is not specified. Use minikts.init(root_dir=...) to set it.")
        result = self.root_dir / ".minikts"
        result.mkdir(exist_ok=True)
        return result
    
    @property
    def is_inside_experiment(self):
        if self.script_path is None:
            return False
        return self.experiments_dir in self.script_path.parents

    def switch_workdir(self, path: Union[Path, str], create: bool = False):
        path = self._convert_resolve_path(path)
        report("ctx", f"Switch workdir: [!path]{shorten_path(self.workdir)}[/] -> [!path]{shorten_path(path)}[/]")
        if create:
            path.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            raise OSError(f"{path} does not exist. Use ctx.switch_workdir(..., create=True) to create it.")
        os.chdir(path)
    
    def copy_sources(self, 
        filenames: Optional[List[str]] = None, 
        src_dir: Optional[Union[str, Path]] = None, 
        dest_dir: Optional[Union[str, Path]] = None, 
    ):
        filenames = filenames or self.tracked_filenames
        src_dir = src_dir or self.src_dir
        dest_dir = dest_dir or self.workdir
        
        for filename in filenames:
            src_file = src_dir / filename
            dest_file = dest_dir / filename
            report("ctx", f"Copy file: [!path]{shorten_path(src_file)}[/] -> [!path]{shorten_path(dest_file)}[/]")
            shutil.copy(src_file, dest_file)
    
    @staticmethod
    def _join_path_assert_exists(path: Path, name: str):
        if path is None or name is None:
            return None
        result = path / name
        if not result.exists():
            return None
        return result
    
    @staticmethod
    def _convert_resolve_path(path: Union[Path, str]):
        return Path(path).expanduser().resolve()

ctx = context = Context()
init = context.__init__

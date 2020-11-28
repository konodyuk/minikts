import abc

import dill
import pandas as pd

from minikts.config import config

class AbstractCache(abc.ABC):
    @abc.abstractmethod
    def save_object(self, obj, key: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def load_object(self, key: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def save_dataframe(self, df, key: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def load_dataframe(self, key: str):
        raise NotImplementedError()

class ProcessCache(AbstractCache):
    """Caches items in scope of current process."""
    def __init__(self):
        self.data = dict()

    def save_object(self, obj, key):
        self.data[key] = obj

    def load_object(self, key):
        return self.data[key]

    def save_dataframe(self, df, key):
        self.save_object(df, key)

    def load_dataframe(self, key):
        return self.load_object(key)

class DiskCache(AbstractCache):
    """Caches items on disk."""
    def save_object(self, obj, key):
        key = self._filter_key(key)
        dill.dump(obj, open(self.dir / (key + ".dill"), "wb"))

    def load_object(self, key):
        key = self._filter_key(key)
        return dill.load(open(self.dir / (key + ".dill"), "rb"))

    def save_dataframe(self, df, key):
        key = self._filter_key(key)
        df.to_parquet(self.dir / (key + ".parquet"))

    def load_dataframe(self, key):
        key = self._filter_key(key)
        return pd.read_parquet(self.dir / (key + ".parquet"))

    @staticmethod
    def _filter_key(key):
        key = key.replace("/", "")
        key = key.replace("\\", "")
        return key

class LocalCache(DiskCache):
    """Caches items in scope of current experiment."""
    @property
    def dir(self):
        res_path = config.paths.experiment_dir / "local_cache"
        res_path.mkdir(exist_ok=True)
        return res_path

class GlobalCache(DiskCache):
    """Caches items in scope of current project."""
    @property
    def dir(self):
        res_path = config.paths.global_cache_dir
        res_path.mkdir(exist_ok=True)
        return res_path

class CombinedCache(AbstractCache):
    def __init__(self, caches):
        self.caches = caches

    def save_object(self, obj, key):
        for cache in self.caches:
            cache.save_object(obj, key)

    def load_object(self, key):
        for cache in self.caches:
            try:
                return cache.load_object(key)
            except:
                pass

    def save_dataframe(self, df, key):
        for cache in self.caches:
            cache.save_dataframe(obj, key)

    def load_dataframe(self, key):
        for cache in self.caches:
            try:
                return cache.load_dataframe(key)
            except:
                pass

process_cache = ProcessCache()
local_cache = LocalCache()
global_cache = GlobalCache()
fast_local_cache = CombinedCache([process_cache, local_cache])
fast_global_cache = CombinedCache([process_cache, global_cache])

import time
import functools

import attr
from box import Box

import numpy as np
import pandas as pd

from minikts.config import register_postload_hook, config

@attr.s
class Profiler:
    callback_options = attr.ib(init=False, factory=dict)
    _data = attr.ib(init=False, factory=functools.partial(Box, default_box=True))
    _pre_callbacks = attr.ib(init=False, factory=list)
    _post_callbacks = attr.ib(init=False, factory=list)
    _final_callbacks = attr.ib(init=False, factory=list)

    def profile(self, **callback_kwargs):
        def wrapper(method):
            method_name = method.__name__
            @functools.wraps(method)
            def _wrapped(*fargs, **fkwargs):
                callback_kwargs.update(self.callback_options)
                method_data = self._data[method_name]
                method_data.name = method_name
                for callback in self._pre_callbacks:
                    callback(method_data, **callback_kwargs)
                result = method(*fargs, **fkwargs)
                for callback in self._post_callbacks:
                    callback(method_data, **callback_kwargs)
                return result
            return _wrapped
        return wrapper

    def report(self, **callback_kwargs):
        for callback in self._final_callbacks:
            callback(self._data, **callback_kwargs)

    def set_option(self, key, value):
        self.callback_options[key] = value

    def pre_callback(self, callback):
        self._pre_callbacks.append(callback)

    def post_callback(self, callback):
        self._post_callbacks.append(callback)

    def final_callback(self, callback):
        self._final_callbacks.append(callback)

profiler = Profiler()
profile = profiler.profile

@register_postload_hook
def set_profiler_options():
    if "profiler" in config:
        for option, value in config.profiler.items():
            profiler.set_option(option, value)

@profiler.pre_callback
def on_start_print(data, verbose=True, **k):
    if not verbose:
        return
    print(f"Step {data.name} started")

@profiler.pre_callback
def on_start_set_timer(data, **k):
    data.start = time.time()

@profiler.pre_callback
def on_start_increase_calls(data, **k):
    if not "calls" in data:
        data.calls = 0
    data.calls += 1

@profiler.post_callback
def on_stop_save_timing(data, **k):
    data.timing = time.time() - data.start
    if "timings" not in data:
        data.timings = list()
    data.timings.append(data.timing)

@profiler.post_callback
def on_stop_print(data, verbose=True, **k):
    if not verbose:
        return
    print(f"Step {data.name} finished, took {data.timing}")

@profiler.final_callback
def on_finish_print(profiler_data, **k):
    timing_report = list()
    for name, method_data in profiler_data.items():
        timing_report.append({
            "name": name,
            "sum_time": np.sum(method_data.timings),
            "n_calls": method_data.calls,
            "mean_time": np.mean(method_data.timings),
            "max_time": np.max(method_data.timings),
        })
    timing_report = pd.DataFrame(timing_report)
    if timing_report.empty:
        return
    timing_report.sort_values("sum_time", inplace=True, ascending=False)
    print(timing_report)

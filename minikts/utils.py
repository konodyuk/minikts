import os
import parse

from minikts.config import config

def find_next_of_format(fmt, paths=None, parent_dir=None):
    if parent_dir is not None:
        assert paths is None
        paths = list(os.listdir(parent_dir))
    assert paths is not None
    used_numbers = list()
    for path in paths:
        result = parse.search(fmt, path)
        if result is not None and len(result.fixed) > 0:
            used_numbers.append(result.fixed[0])
    used_numbers = sorted(used_numbers)
    next_number = 0
    while (next_number < len(used_numbers)
           and next_number == used_numbers[next_number]):
        next_number += 1
    if parent_dir is None:
        return fmt.format(next_number)
    return parent_dir / fmt.format(next_number)

def get_experiment_path(experiment_id):
    return config.paths.experiments_dir / experiment_id

def hash_dataframe(df):
    raise NotImplementedError()

def hash_source(function):
    raise NotImplementedError()

def _flatten_box(b):
    return {key: b[key] for key in b.keys(dotted=True)}

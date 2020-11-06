import importlib

from minikts.config import init, load_config

def debug(main_path, config_path):
    """Imports everything from main and loads config from config_path. Namespace is returned as a module"""
    spec = importlib.util.spec_from_file_location("main", main_path)
    main = importlib.util.module_from_spec(spec)
    init(main_path)
    load_config(config_path)
    spec.loader.exec_module(main)
    return main

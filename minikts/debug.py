import importlib
from pathlib import Path

def debug(source_dir=None, main_path=None, config_path=None):
    raise NotImplementedError()
    """Imports experiment source as a module

    Args:
        source_dir: directory containing main.py and config.yaml
        main_path: path of main.py, if not provided, set to source_dir/main.py
        config_path: path of config.yaml, if not provided, set to source_dir/config.yaml

    Returns:
        Namespace of the experiment

    Examples:
        >>> import minikts.api as kts
        >>> main = kts.debug("../src")
        >>> exp = main.CatBoostTemplateExperiment()
        >>> exp.ensemble(experiment_ids=[15, 20])
    """
    if source_dir is not None:
        assert main_path is None, "If source_dir is provided, main_path should be None"
        assert config_path is None, "If source_dir is provided, config_path should be None"
        source_dir = Path(source_dir)
        main_path = source_dir / "main.py"
        config_path = source_dir / "config.yaml"
    else:
        assert main_path is not None, "main_path is not provided"
        assert config_path is not None, "config_path is not provided"
        main_path = Path(main_path)
        config_path = Path(config_path)
    assert main_path.exists(), f"main_path ({main_path}) does not exist"
    assert config_path.exists(), f"config_path ({config_path}) does not exist"
    spec = importlib.util.spec_from_file_location("main", main_path)
    main = importlib.util.module_from_spec(spec)
    init(main_path)
    load_config(config_path)
    spec.loader.exec_module(main)
    return main

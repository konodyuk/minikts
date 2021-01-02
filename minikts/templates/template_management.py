import os
import shutil
import pkg_resources
from pathlib import Path

TEMPLATES = [
    "catboost",
    "pytorch_lightning",
]

TEMPLATE_FILES = [
    "main.py",
    "config.yaml",
    "requirements.txt",
]

REQUIRED_DIRS = [
    "src",
    "experiments",
    "global_cache",
]

def init_template(template_name):
    assert template_name in TEMPLATES
    cwd = Path(".").resolve()
    for dirname in REQUIRED_DIRS:
        if (cwd / dirname).exists():
            assert len(os.listdir(cwd / dirname)) == 0, f"{cwd / dirname} already exists and is not empty"
        else:
            (cwd / dirname).mkdir()

    source_dir = cwd / "src"
    for filename in TEMPLATE_FILES:
        path = get_resource_path(template_name, filename)
        shutil.copy(path, source_dir / filename)

def get_resource_path(template_name, filename):
    templates_path = pkg_resources.resource_filename("minikts", "templates")
    templates_path = Path(templates_path)
    return templates_path / template_name / filename

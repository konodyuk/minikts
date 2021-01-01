from typing import Optional

try:
    import neptune
except ImportError:
    neptune = None

from minikts.config import config, hparams
from minikts.utils import _flatten_box
from minikts.context import ctx

class NeptuneLogger:
    def __init__(self, 
        api_token: Optional[str] = None,
        project_name: Optional[str] = None, 
        tags: Optional[str] = None,
        verbose: bool = False,
        dry_run: bool = False,
        **kwargs,
    ):
        self.api_token = api_token
        self.project_name = project_name
        self.tags = tags
        self.verbose = verbose
        self.dry_run = dry_run
        self.kwargs = kwargs
        self.experiment = self.create_experiment()

    @property
    def id(self):
        if ctx.is_inside_experiment:
            return ctx.script_path.parent.name
        if self.dry_run:
            return "debug"
        return self.experiment.id

    def log_metric(self, log_name, x, y=None, timestamp=None):
        if self.verbose:
            print(f"log_metric({log_name}, {x}, {y})")
            return
        self.experiment.log_metric(log_name, x, y, timestamp)

    def log_text(self, log_name, x, y=None, timestamp=None):
        if self.verbose:
            print(f"log_text({log_name}, {x}, {y})")
            return
        self.experiment.log_text(log_name, x, y, timestamp)

    def log_image(self, log_name, x, y=None, image_name=None, description=None, timestamp=None):
        if self.verbose:
            x = x.shape if hasattr(x, 'shape') else None
            y = y.shape if hasattr(y, 'shape') else None
            print(f"log_image({log_name}, {x}, {y})")
            return
        self.experiment.log_image(log_name, x, y, image_name, description, timestamp)

    def log_artifact(self, artifact, destination=None):
        if self.verbose:
            print(f"log_artifact()")
            return
        self.experiment.log_artifact(artifact, destination)

    def create_experiment(self):
        if self.dry_run:
            neptune.init(
                project_qualified_name="dry-run/debug",
                backend=neptune.OfflineBackend()
            )
        else:
            neptune.init(
                api_token=self.api_token,
                project_qualified_name=self.project_name,
            )

        ctx.copy_sources(dest_dir=ctx.tmp_dir)
        ctx.switch_workdir(ctx.tmp_dir)
        self.experiment = neptune.create_experiment(
            tags=self.tags,
            params=_flatten_box(hparams),
            upload_source_files=list(ctx.tracked_filenames),
            **self.kwargs,
        )
        if ctx.experiments_dir is not None:
            ctx.switch_workdir(ctx.experiments_dir / self.id, create=True)

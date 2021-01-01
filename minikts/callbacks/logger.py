class LoggerCallback:
    def __init__(self, *args, logger, ignore_keys=["step"], **kwargs):
        self.args = args
        self.ignore_keys = ignore_keys
        self.logger = logger
        self.kwargs = kwargs
        self.suffix = '_'.join(list(map(str, args))) 
        self.suffix += '_'.join([f"{key}={value}" for key, value in kwargs.items()])

    def __call__(self, report):
        step = report.get("step", None)
        for key, value in report.items():
            if key in self.ignore_keys:
                continue
            fmt_key = f"{key}_{self.suffix}"
            if step is not None:
                self.logger.log_metric(fmt_key, step, value)
            else:
                self.logger.log_metric(fmt_key, value)

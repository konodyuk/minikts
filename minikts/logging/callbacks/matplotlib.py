import attr
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
try:
    from IPython.display import clear_output
except:
    clear_output = None


@attr.s
class MatplotlibCallback:
    """Plots training curves in Jupyter notebooks

    Args:
        interval: update interval in steps
        figsize: figsize of plot

    Returns:
        Callback redrawing training curves each `interval` steps

    Examples:
        >>> %pylab inline
        >>> import minikts.api as kts
        >>> from lightgbm import LGBMClassifier
        >>> with kts.parse_stdout(kts.patterns.lightgbm, kts.MatplotlibCallback(interval=50)):
        ...     model = LGBMClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train, eval_set=[(x_train, y_train), (x_test, y_test)])
    """
    interval = attr.ib(default=5)
    figsize = attr.ib(default=(7, 5))
    _buf = attr.ib(factory=list, init=False)
    _last_update = attr.ib(default=-1, init=False)
    _last_step = attr.ib(default=-1, init=False)
    _keys = attr.ib(factory=set, init=False)
    def _attrs_post_init_(self):
        if plt is None:
            raise ImportError("MatplotlibCallback is available only if matplotlib is installed. "
                              "Install it with `pip install matplotlib`.")
        if clear_output is None:
            raise ImportError("MatplotlibCallback is available only in Jupyter environment.")

    def __call__(self, report):
        self.append(report)
        if self._last_step - self._last_update >= self.interval:
            self.draw()
            self._last_update = self._last_step
    
    def append(self, report):
        step = report.get('step', -1)
        if step <= self._last_step:
            return
        self._buf.append(report)
        self._last_step = max(self._last_step, step)
        self._keys |= set(report.keys())
    
    def draw(self):
        plt.figure(figsize=self.figsize)
        for key in self._keys:
            if key == 'step':
                continue
            steps = list()
            values = list()
            for report in self._buf:
                if "step" in report and key in report:
                    steps.append(report["step"])
                    values.append(report[key])
            plt.plot(steps, values, label=key)
        plt.legend()
        clear_output(wait=True)
        plt.show()

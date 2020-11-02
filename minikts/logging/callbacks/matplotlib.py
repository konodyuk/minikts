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
    interval = attr.ib(default=5)
    figsize = attr.ib(default=(7, 5))
    buf = attr.ib(factory=list)
    last_update = attr.ib(default=-1)
    last_step = attr.ib(default=-1)
    keys = attr.ib(factory=set)
    def _attrs_post_init_(self):
        if plt is None:
            raise ImportError("MatplotlibCallback is available only if matplotlib is installed. "
                              "Install it with `pip install matplotlib`.")
        if IPython is None:
            raise ImportError("MatplotlibCallback is available only in Jupyter environment.")

    def __call__(self, report):
        self.append(report)
        if self.last_step - self.last_update >= self.interval:
            self.draw()
            self.last_update = self.last_step
    
    def append(self, report):
        step = report.get('step', -1)
        if step <= self.last_step:
            return
        self.buf.append(report)
        self.last_step = max(self.last_step, step)
        self.keys |= set(report.keys())
    
    def draw(self):
        plt.figure(figsize=self.figsize)
        for key in self.keys:
            if key == 'step':
                continue
            steps = list()
            values = list()
            for report in self.buf:
                if "step" in report and key in report:
                    steps.append(report["step"])
                    values.append(report[key])
            plt.plot(steps, values, label=key)
        plt.legend()
        clear_output(wait=True)
        plt.show()

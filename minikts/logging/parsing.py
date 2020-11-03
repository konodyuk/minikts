import sys
import attr
import parse
from contextlib import redirect_stdout

original_stdout = sys.stdout

@attr.s()
class StreamParser:
    patterns = attr.ib()
    buf = attr.ib(factory=str, init=False)
    callbacks = attr.ib(default=[print])

    def write(self, b):
        self.buf += b
        if self.buf.find('\n') != -1:
            self.flush()
            
    def flush(self):
        for line in self.buf.strip().split('\n'):
            line_result = dict()
            for pattern in self.patterns:
                pattern_result = parse.search(pattern, line)
                if pattern_result is None:
                    continue
                line_result = {**line_result, **pattern_result.named}
            with redirect_stdout(original_stdout):
                for callback in self.callbacks:
                    callback(line_result)
        self.buf = str()

def parse_stdout(patterns, *callbacks):
    """Parses each stdout line in line with `patterns` argument and sequentially calls callbacks

    Args:
        patterns: tuple of patterns compatible with `parse.search` function
        *callbacks: 
            any functions or functors to be called from result of pattern search,
            order matters, as callbacks can modify the pattern search dictionary

    Returns:
        Context manager redirecting stdout and parsing it line-by-line

    Examples:
        >>> import minikts.api as kts
        >>> from lightgbm import LGBMClassifier
        >>> with kts.parse_stdout(kts.patterns.lightgbm, kts.MatplotlibCallback(interval=50)):
        ...     model = LGBMClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train, eval_set=[(x_train, y_train), (x_test, y_test)])
    """
    return redirect_stdout(StreamParser(patterns, callbacks=callbacks))

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

class Patterns:
    """Common patterns for stdout parsing

    Examples:
        >>> import minikts.api as kts
        >>> from lightgbm import LGBMClassifier
        >>> with kts.parse_stdout(kts.patterns.lightgbm, kts.MatplotlibCallback(interval=50)):
        ...     model = LGBMClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train, eval_set=[(x_train, y_train), (x_test, y_test)])
        >>> with kts.parse_stdout(kts.patterns.lightgbm_valid_only, kts.MatplotlibCallback(interval=50)):
        ...     model = LGBMClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train, eval_set=[(x_test, y_test)])

        >>> from catboost import CatBoostClassifier
        >>> with kts.parse_stdout(kts.patterns.catboost, kts.MatplotlibCallback(interval=50)):
        ...     model = CatBoostClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train, eval_set=(x_test, y_test)])
        >>> with kts.parse_stdout(kts.patterns.catboost, kts.MatplotlibCallback(interval=50)):
        ...     model = CatBoostClassifier(n_estimators=1000)
        ...     model.fit(x_train, y_train])

        >>> from lightfm import LightFM
        >>> with kts.parse_stdout(kts.patterns.lightfm, kts.MatplotlibCallback(interval=2)):
        ...     model = LightFM()
        ...     model.fit(interactions, epochs=100, verbose=True)
    """

    catboost = ("learn: {train:g}", "test: {valid:g}", "{step:d}:")
    xgboost_valid_only = ("valid{}:{valid:g}", "[{step:d}]")
    lightgbm_valid_only = ("valid{}:{valid:g}", "[{step:d}]")
    xgboost = ("valid{}0{}:{train:g}", "valid{}1{}:{valid:g}", "[{step:d}]")
    lightgbm = ("valid{}0{}:{train:g}", "valid{}1{}:{valid:g}", "[{step:d}]")
    lightfm = ("{}{epoch:d}", "{}{step:d}")

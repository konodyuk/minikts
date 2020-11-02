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
    return redirect_stdout(StreamParser(patterns, callbacks=callbacks))

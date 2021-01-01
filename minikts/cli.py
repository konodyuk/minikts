import abc
import click
import functools

from minikts.context import ctx

class CLIMeta(abc.ABCMeta):
    def __new__(cls, name, bases, members):
        click_params = members["__click_params__"] = dict()
        for base in bases:
            if hasattr(base, "__click_params__"):
                click_params.update(base.__click_params__)
        for name, member in members.items():
            if hasattr(member, "__click_params__"):
                click_params[name] = member.__click_params__
        return abc.ABCMeta.__new__(cls, name, bases, members)
    
def wrap(method, click_params):
    @functools.wraps(method)
    def wrapped(*args, **kwargs):
        return method(*args, **kwargs)
    setattr(wrapped, "__click_params__", click_params)
    return wrapped

class CLI(metaclass=CLIMeta):
    """Turns all methods that have click options into CLI endpoints

    Examples:
        >>> class Experiment(CLI):
        ...     @click.option(...)
        ...     def train(...):
        ...         ...
        ...     @click.option(...)
        ...     def predict(...):
        ...         ...
        >>> if __name__ == "__main__":
        ...     exp = Experiment()
        ...     exp.run()

        >>> class Runner(CLI):
        ...     @click.option(...)
        ...     def submit(...):
        ...         ...
        ...     @click.option(...)
        ...     def blend(...):
        ...         ...
        >>> if __name__ == "__main__":
        ...     Runner().run()
    """
    def run(self, **kwargs):
        @click.group(chain=True)
        def _cli():
            pass
        
        for name, params in self.__click_params__.items():
            method = getattr(self, name)
            wrapped = wrap(method, params)
            _cli.command(name)(wrapped)
            
        _cli(standalone_mode=False, **kwargs)

def config_option(arg_name="config_path"):
    result = click.option(
        "--config",
        arg_name,
        default=ctx.script_path.parent / "config.yaml",
        show_default=True,
        type=click.Path(
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True
        ),
    )
    return result

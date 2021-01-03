import attr
import libtmux
from typing import Optional

from minikts.monitoring import report

@attr.s
class Tmux:
    server = attr.ib(factory=libtmux.Server)
    
    def get_or_create_session(self, name: str):
        session = self.server.find_where({"session_name": name})
        created = False
        if session is None:
            report("tmux", f"Creating session [bold]{name}[/]")
            session = self.server.new_session(name)
            created = True
        return session, created

@attr.s
class Session:
    """Tmux session wrapper
    
    Args:
        name: session name
    """
    name = attr.ib(type=str)
    tmux = attr.ib(factory=Tmux, init=False, repr=False)
    def __attrs_post_init__(self):
        self._session, created = self.tmux.get_or_create_session(self.name)
        if created:
            self.shift_all_windows(100)
        
    def get_or_create_window(self, name: str, index: Optional[int] = None):
        """Returns a window with specified name and index
        
        In case if window exists with the right name and index, returns it.
        If its index is not equal to the passed one, tries to move it.
        Creates a new window if none has the specified name.
        
        Args:
            name: window name
            index: desired window index
            
        Returns:
            libtmux.Window object
        """
        windows = self._session.windows
        for window in windows:
            if window.name == name:
                if index is not None and window.index != str(index):
                    window.move_window(index)
                return window
        report("tmux", f"Creating window [bold]{name}[/] in session [bold]{name}[/]")
        return self._session.new_window(window_name=name, window_index=index, attach=False)
    
    def shift_all_windows(self, index_delta: int):
        """Shifts indices of all windows in the session by index_delta
        
        Args:
            index_delta: shift length
        """
        for window in self._session.windows:
            old_index = int(window.index)
            new_index = old_index + index_delta
            report("tmux", f"Moving window [bold]{window.name}[/] from index [bold]{old_index}[/] to [bold]{new_index}[/] in session [bold]{name}[/]")
            window.move_window(new_index)
            
    def close_windows(self):
        """Closes all windows in the session
        
        Leaves only one tmux-keep window at position 100 to prevent session from being closed.
        """
        sentinel = "tmux-keep"
        self.get_or_create_window(name=sentinel, index=100)
        for window in self._session.windows:
            if window.name != sentinel:
                report("tmux", f"[red]Killing[/] window [bold]{window.name}[/] in session [bold]{name}[/]")
                window.kill_window()

@attr.s
class Window:
    """Tmux window wrapper
    
    Args:
        session_name: name of parent session
        window_name: window name
        window_index: desired window index
    """
    session_name = attr.ib(type=str)
    window_name = attr.ib(type=str)
    window_index = attr.ib(default="", type=int)
    def __attrs_post_init__(self):
        self.session = Session(self.session_name)
        self._window = self.session.get_or_create_window(name=self.window_name, index=self.window_index)
        
    def run(self, cmd: str):
        """Runs command in window
        
        Args:
            cmd: command
        """
        report("tmux", f"[{self.session_name}/{self.window_name}] $ {cmd}")
        self._window.attached_pane.send_keys(cmd)
        
    def move(self, index: int):
        """Moves window to index
        
        Args:
            index: desired index
        """
        report("tmux", f"Moving window [bold]{self.window_name}[/] from index [bold]{self._window.index}[/] to [bold]{index}[/] in session [bold]{self.session_name}[/]")
        self._window.move_window(index)
        self.window_index = index

@attr.s
class GPUWindow:
    """Interface for a special window in session, serving a specified GPU
    
    Creates a window with index equal to GPU index and name "gpu-{index}".
    Only specified GPU is available to processes running in the window.
    
    Args:
        session_name: name of parent session
        gpu: index of GPU to isolate

    Examples:
        >>> for i in range(5):
        ...     w = GPUWindow("competition-name", i)
        ...     w.run(f"python3 /path/to/main.py train --fold {i}")
    """
    session_name = attr.ib(type=str)
    gpu = attr.ib(type=int)
    def __attrs_post_init__(self):
        self.name = f"gpu-{self.gpu}"
        self.index = self.gpu
        self.setup_cmd = f"export CUDA_VISIBLE_DEVICES={self.gpu}"
        self.window = Window(session_name=self.session_name, window_name=self.name, window_index=self.index)

    def run(self, cmd: str):
        """Runs command in window, exposing only specified GPU to it
        
        Args:
            cmd: command
        """
        cmd = f"{self.setup_cmd} && {cmd}"
        self.window.run(cmd)

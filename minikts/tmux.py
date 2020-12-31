import  attr
import libtmux

@attr.s
class Tmux:
    server = attr.ib(factory=libtmux.Server)
    
    def get_or_create_session(self, name: str):
        session = self.server.find_where({"session_name": name})
        if session is None:
            session = self.server.new_session(name)
        return session
    
    def exec_in_session(self, cmd: str, session_name: str):
        session = self.get_or_create_session(session_name)
        session.attached_pane.send_keys(cmd)

@attr.s
class Session:
    name = attr.ib(type=str)
    tmux = attr.ib(factory=Tmux, init=False, repr=False)

    def run(self, cmd: str):
        print(f"[{self.name}] $ {cmd}")
        self.tmux.exec_in_session(cmd, self.name)

@attr.s
class GPUSession:
    gpu = attr.ib(type=int)
    def _attrs_post_init_(self):
        self.name = f"{self.name}-{self.gpu}"
        self.setup_cmd = f"export CUDA_VISIBLE_DEVICES={self.gpu}"

    def run(self, cmd: str):
        cmd = f"{self.setup_cmd} && {cmd}"
        super().run(cmd)

from typing import List, Optional
from rich.text import Text
from rich.tree import Tree


class StdTree:
    _stdout_text: Optional[Text]
    _stdout_str: List[str]
    _stderr_text: Optional[Text]
    _stderr_str: List[str]

    def __init__(self, cmd: str) -> None:
        self.tree = Tree("", hide_root=True)
        self.cmd = cmd
        self.tree.add(cmd)
        self._stdout_text = None
        self._stderr_text = None
        self._stdout_str = []
        self._stderr_str = []

    def set_stdout(self, stdout: List[str]):
        if not stdout:
            return

        if not self._stdout_text:
            self._stdout_text = Text("", style="dim")
            stdout_branch = self.tree.add("stdout")
            stdout_branch.add(self._stdout_text)

            if self._stderr_text:
                # Swap the children so that stdout is always first
                self.tree.children = [self.tree.children[1], self.tree.children[0]]

        self._stdout_str = stdout
        self._stdout_text.plain = "\n".join(stdout)

    def set_stderr(self, stderr: List[str]):
        if not stderr:
            return

        if not self._stderr_text:
            self._stderr_text = Text("", style="red")
            stderr_branch = self.tree.add("stderr")
            stderr_branch.add(self._stderr_text)
            self._stderr_str = stderr

        self._stderr_str = stderr
        self._stderr_text.plain = "\n".join(stderr)

    def reset(self):
        self._stdout_text = None
        self._stderr_text = None
        self._stdout_str = []
        self._stderr_str = []
        self.tree.children = []
        self.tree.add(self.cmd)

    def height(self) -> int:
        stdout_height = len(self._stdout_str) + 1 if self._stdout_str else 0
        stderr_height = len(self._stderr_str) + 1 if self._stderr_str else 0
        cmd_height = 1

        return cmd_height + stdout_height + stderr_height


class Padder:
    def __init__(self) -> None:
        self._max_padding = 0

    def get_padding(self, tree: StdTree) -> int:
        height = tree.height()
        self._max_padding = max(self._max_padding, height)
        return self._max_padding - height

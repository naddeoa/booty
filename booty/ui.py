from typing import Optional
from rich.text import Text
from rich.tree import Tree


class StdTree:
    _stdout_text: Optional[Text]
    _stderr_text: Optional[Text]

    def __init__(self, cmd: str) -> None:
        self.tree = Tree("", hide_root=True)
        self.cmd = cmd
        self.tree.add(cmd)
        self._stdout_text = None
        self._stderr_text = None

    def set_stdout(self, stdout: str):
        if not stdout:
            return

        if not self._stdout_text:
            self._stdout_text = Text("", style="dim")
            stdout_branch = self.tree.add("stdout")
            stdout_branch.add(self._stdout_text)

        self._stdout_text.plain = stdout

    def set_stderr(self, stderr: str):
        if not stderr:
            return

        if not self._stderr_text:
            self._stderr_text = Text("", style="red")
            stderr_branch = self.tree.add("stderr")
            stderr_branch.add(self._stderr_text)

        self._stderr_text.plain = stderr

    def reset(self):
        self._stdout_text = None
        self._stderr_text = None
        self.tree.children = []
        self.tree.add(self.cmd)

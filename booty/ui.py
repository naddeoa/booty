from typing import Any, Callable, List, Optional, Union
from datetime import datetime
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
                # In this case, there will be 3 things in the tree.
                # 0 - the cmd from init
                # 1 - the stderr branch since it was apparently added first
                # 2 - the stdout branch we just added
                self.tree.children = [self.tree.children[2], self.tree.children[1]]

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


class UpdateTracker:
    """
    Class to enable dynamic updates on the UI tables. By default, rich allows you to set a refresh rate or trigger manual
    updates. This makes manual updates more performant by doing quick 'dirty' checks to determine if updating ins required. Updating
    is technically always required because the table's 'elapsed time' column always changes, but we don't want to update the table just
    because of that.

    This class tracks some state and has a min/max ms time config to keep the table looking responsive without updating too often. The
    driver for this was my CPU usage while the installer was running, paired with the size of the asciinema files that were generated
    because of frequent updates. Obviously, the more frequent the update the better the table looks, but that's the trade off.

    """

    def __init__(self, max_update_timeout_ms: float = 5000, min_update_ms: float = 200) -> None:
        """
        Args:
            max_update_timeout_ms: The maximum amount of time in milliseconds that can pass before an update is forced. This is useful
            because the table usually contains an 'elapsed time' column that should update fairly frequently regardless of everything else.
            min_update_ms: The minimum amount of time in milliseconds that must pass before an update is allowed. This prevents updates
            from getting too frequent.
        """
        self._timeout_ms = max_update_timeout_ms
        self._min_update_ms = min_update_ms
        self._last_update_timestamp_ms = datetime.now().timestamp() * 1000
        self._last_update_state: List[Any] = []

    def max_update_time_passed(self, now: float) -> bool:
        if now - self._last_update_timestamp_ms > self._timeout_ms:
            return True
        return False

    def min_update_time_passed(self, now: float) -> bool:
        if now - self._last_update_timestamp_ms > self._min_update_ms:
            return True
        return False

    def _update(self, now: float, update_fn: Callable[[], None], state: List[Union[str, List[str]]]):
        update_fn()
        self._last_update_timestamp_ms = now
        self._last_update_state = state

    def update(self, update_fn: Callable[[], None], state: List[Union[str, List[str]]]):
        now = datetime.now().timestamp() * 1000

        if self.min_update_time_passed(now) and state != self._last_update_state:
            self._update(now, update_fn, state)
        elif self.max_update_time_passed(now):
            self._update(now, update_fn, state)

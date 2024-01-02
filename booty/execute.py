from subprocess import Popen, PIPE
from select import select
import shutil
from typing import Dict, Generator, List, Literal, Optional, Sequence, Tuple
from lark import ParseTree
from dataclasses import dataclass, field
from booty.ast_util import ExecutableIndex, RecipeDefinitionIndex, DependencyIndex
from booty.graph import DependencyGraph
from booty.types import Executable, ShellCommand


@dataclass
class BootyData:
    execution_index: ExecutableIndex
    dependency_index: DependencyIndex
    recipe_index: RecipeDefinitionIndex
    G: DependencyGraph
    ast: ParseTree


@dataclass
class ExecuteError(Exception):
    code: int


def get_commands(data: BootyData, method: Literal["setup", "is_setup"]) -> Dict[str, Sequence[str]]:
    commands: Dict[str, Sequence[str]] = {}

    for target in data.execution_index:
        exec = data.execution_index[target]
        cmds = _get_setup_commands(data, exec) if method == "setup" else _get_is_setup_commands(data, exec)
        current_cmds = commands.get(target, [])
        new_cmds = [*current_cmds, *cmds]
        commands[target] = new_cmds

    return commands


def execute(
    data: BootyData, target: str, method: Literal["setup", "is_setup"]
) -> Generator[Tuple[Optional[str], Optional[str]], None, None]:
    bash = shutil.which("bash")
    exec = data.execution_index[target]
    if method == "setup":
        commands = _get_setup_commands(data, exec)
    elif method == "is_setup":
        commands = _get_is_setup_commands(data, exec)

    if bash is None:
        raise RuntimeError("bash not found in PATH")

    for command in commands:
        with Popen([bash, "-c", command], stdout=PIPE, stderr=PIPE, text=True, bufsize=1) as proc:
            while True:
                if proc.stdout is None or proc.stderr is None:
                    # This shouldn't be possible since I'm calling Popen with PIPE
                    raise RuntimeError("stdout or stderr is None")

                rdy_out, _, _ = select([proc.stdout], [], [], 0.1)
                out = proc.stdout.readline().strip() if rdy_out else None

                rdy_err, _, _ = select([proc.stderr], [], [], 0.1)
                err = proc.stderr.readline().strip() if rdy_err else None

                yield (out, err)

                if proc.poll() is not None:
                    out = proc.stdout.readline().strip()
                    err = proc.stderr.readline().strip()
                    yield (out, err)
                    break

        if proc.returncode != 0:
            raise ExecuteError(proc.returncode)


def _get_setup_commands(data: BootyData, it: Dict[str, List[Executable]]) -> List[str]:
    exec = it["setup"] if "setup" in it else it["recipe"]

    execs: List[str] = []
    for e in exec:
        if isinstance(e, ShellCommand):
            execs.append(e.command)
        else:
            recipe_name = e.name
            args = e.args
            recipe = data.recipe_index[recipe_name]

            for command in recipe.iter_commands(args, recipe.defs["setup"], data.recipe_index, "setup"):
                execs.append(command)

    return execs


def _get_is_setup_commands(data: BootyData, it: Dict[str, List[Executable]]) -> List[str]:
    exec = it["is_setup"] if "is_setup" in it else it["recipe"]

    execs: List[str] = []
    for e in exec:
        if isinstance(e, ShellCommand):
            execs.append(e.command)
        else:
            recipe_name = e.name
            args = e.args
            recipe = data.recipe_index[recipe_name]

            for command in recipe.iter_commands(args, recipe.defs["is_setup"], data.recipe_index, "is_setup"):
                execs.append(command)

    return execs


@dataclass
class CommandExecutor:
    data: BootyData
    target: str
    method: Literal["setup", "is_setup"]

    stdout: List[str] = field(default_factory=list)
    stderr: List[str] = field(default_factory=list)
    code: int = -1

    def execute(self) -> Generator[Tuple[Optional[str], Optional[str]], None, None]:
        try:
            for out, err in execute(self.data, self.target, self.method):
                if out:
                    self.stdout.append(out)
                if err:
                    self.stderr.append(err)
                yield (out, err)

            self.code = 0
        except ExecuteError as e:
            self.code = e.code

    def stdout_summary(self) -> str:
        return "\n".join(self.stdout)

    def stderr_summary(self) -> str:
        return "\n".join(self.stderr)

    def all_stdout(self) -> str:
        return "\n".join(self.stdout)

    def all_stderr(self) -> str:
        return "\n".join(self.stderr)

    def latest_stdout(self, tail_n: int = 5) -> List[str]:
        return self.stdout[-tail_n:]

    def latest_stderr(self, tail_n: int = 5) -> List[str]:
        return self.stderr[-tail_n:]

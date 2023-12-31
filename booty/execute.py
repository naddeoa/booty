from subprocess import CalledProcessError, Popen, PIPE
from select import select
import shutil
from typing import Callable, Dict, Generator, List, Literal, Optional, Tuple
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


def check_status_all(data: BootyData) -> Dict[str, Optional[CalledProcessError]]:
    results: Dict[str, Optional[CalledProcessError]] = {}
    for target in list(data.G.iterator()):
        # print(target)
        exec = data.execution_index[target]

        # print(exec)
        commands = _get_is_setup(data, exec)
        for command in commands:
            try:
                command()
                results[target] = None
            except CalledProcessError as e:
                results[target] = e

    return results


def check_target_status(data: BootyData, target: str) -> Optional[CalledProcessError]:
    exec = data.execution_index[target]
    commands = _get_is_setup(data, exec)
    for command in commands:
        try:
            command()
        except CalledProcessError as e:
            return e


def _get_is_setup(data: BootyData, it: Dict[str, List[Executable]]) -> List[Callable[[], None]]:
    exec = it["is_setup"] if "is_setup" in it else it["recipe"]

    execs: List[Callable[[], None]] = []
    for e in exec:
        if isinstance(e, ShellCommand):
            a = e  # whut
            execs.append(lambda: a.execute())
        else:
            recipe_name = e.name
            args = e.args
            recipe_definition = data.recipe_index[recipe_name]
            execs.append(lambda: recipe_definition.is_setup(args, data.recipe_index))

    return execs


@dataclass
class ExecuteError(Exception):
    code: int


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
                    # also check if stdout and stderr are empty
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

    def latest_stdout(self, tail_n: int = 5) -> str:
        return "\n".join(self.stdout[-tail_n:])

    def latest_stderr(self, tail_n: int = 5) -> str:
        return "\n".join(self.stderr[-tail_n:])

    def latest(self, tail_n: int = 5) -> str:
        out = self.latest_stdout(tail_n)
        err = self.latest_stderr(tail_n)
        return r"""
stdout:
{out}

stderr:
{err}
        """.format(out=out, err=err)

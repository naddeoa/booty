from subprocess import CalledProcessError
from typing import Callable, Dict, List, Optional
from lark import ParseTree
import networkx as nx
from dataclasses import dataclass
from booty.ast_util import ExecutableIndex, RecipeDefinitionIndex, DependencyIndex
from booty.dependencies import bfs_iterator
from booty.types import Executable, ShellCommand


@dataclass
class SystemconfData:
    execution_index: ExecutableIndex
    dependency_index: DependencyIndex
    recipe_index: RecipeDefinitionIndex
    G: nx.DiGraph
    ast: ParseTree


def check_status_all(data: SystemconfData) -> Dict[str, Optional[CalledProcessError]]:
    bst_iterator = bfs_iterator(data.G)

    results: Dict[str, Optional[CalledProcessError]] = {}
    for target in bst_iterator:
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


def check_target_status(data: SystemconfData, target: str) -> Optional[CalledProcessError]:
    exec = data.execution_index[target]
    commands = _get_is_setup(data, exec)
    for command in commands:
        try:
            command()
        except CalledProcessError as e:
            return e


def _get_is_setup(data: SystemconfData, it: Dict[str, List[Executable]]) -> List[Callable[[], None]]:
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


def install_target(data: SystemconfData, target: str) -> Optional[CalledProcessError]:
    exec = data.execution_index[target]
    commands = _get_setup(data, exec)
    for command in commands:
        try:
            command()
        except CalledProcessError as e:
            return e


def _get_setup(data: SystemconfData, it: Dict[str, List[Executable]]) -> List[Callable[[], None]]:
    exec = it["setup"] if "setup" in it else it["recipe"]

    execs: List[Callable[[], None]] = []
    for e in exec:
        if isinstance(e, ShellCommand):
            a = e  # whut
            execs.append(lambda: a.execute())
        else:
            recipe_name = e.name
            args = e.args
            recipe_definition = data.recipe_index[recipe_name]
            execs.append(lambda: recipe_definition.setup(args, data.recipe_index))

    return execs

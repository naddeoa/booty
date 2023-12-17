from typing import Callable, Dict, List
from lark import ParseTree
import networkx as nx
from dataclasses import dataclass
from systemconf.ast_util import ExecutableIndex, RecipeDefinitionIndex, get_dependencies, get_zero_dependency_targets
from systemconf.dependencies import bfs_iterator
from systemconf.types import Executable, ShellCommand


@dataclass
class SystemconfData:
    execution_index: ExecutableIndex
    recipe_index: RecipeDefinitionIndex
    G: nx.DiGraph
    ast: ParseTree


def check_status(data: SystemconfData) -> None:
    target_index = get_dependencies(data.ast)
    no_dependency_target_names = get_zero_dependency_targets(target_index)
    bst_iterator = bfs_iterator(data.G, no_dependency_target_names[0])

    for target in bst_iterator:
        # print(target)
        exec = data.execution_index[target]

        # print(exec)
        commands = get_is_setup(data, exec)
        for command in commands:
            command()

        # recipe.setup([], data.recipe_index)


def get_is_setup(data: SystemconfData, it: Dict[str, List[Executable]]) -> List[Callable[[], bool]]:
    exec = it["is_setup"] if "is_setup" in it else it["recipe"]

    execs: List[Callable[[], bool]] = []
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

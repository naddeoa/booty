from systemconf.ast_util import get_dependencies, get_zero_dependency_targets
from systemconf.dependencies import bfs_iterator, has_cycles
from systemconf.execute import SystemconfData


def validate(data: SystemconfData) -> None:
    target_index = get_dependencies(data.ast)
    no_dependency_target_names = get_zero_dependency_targets(target_index)
    bst_iterator = bfs_iterator(data.G, no_dependency_target_names[0])

    for target in bst_iterator:
        print(target)
        exec = data.execution_index.get(target)
        if exec is None:
            raise Exception(f"Missing definition for target '{target}', don't know how to install.")

        # it can eitherh invoke a recipe or define an invocation explicitly
        if "recipe" in exec:
            if len(exec["recipe"]) == 0:
                raise Exception(f"Recipe for target '{target}' is empty, don't know how to install.")
        else:
            if "setup" not in exec:
                print(exec)
                raise Exception(f"Missing setup method for target '{target}', don't know how to install.")

            if len(exec["setup"]) == 0:
                raise Exception(f"Setup for target '{target}' is empty, don't know how to install.")

            if "is_setup" not in exec:
                raise Exception(f"Executable '{target}' has no is_setup, don't know how to test for install status.")

            if len(exec["is_setup"]) == 0:
                raise Exception(f"Executable '{target}' has empty is_setup, don't know how to test for install status.")

    cycles = has_cycles(data.G)
    if len(cycles) > 0:
        raise Exception(f"Cycles detected in dependency graph, cannot continue. {cycles}")

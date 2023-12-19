from booty.dependencies import bfs_iterator, has_cycles
from booty.execute import SystemconfData
from booty.types import RecipeInvocation


def validate(data: SystemconfData) -> None:
    bst_iterator = bfs_iterator(data.G)

    for target in bst_iterator:
        exec = data.execution_index.get(target)
        if exec is None:
            raise Exception(f"Missing definition for target '{target}', don't know how to install.")

        # it can either invoke a recipe or define an invocation explicitly
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

    # validate that all recipe invocations ivoke recipe that exist
    for target, exec in data.execution_index.items():
        if "recipe" in exec:
            for executable in exec["recipe"]:
                if isinstance(executable, RecipeInvocation) and executable.name not in data.recipe_index:
                    raise Exception(f"Recipe '{executable.name}' invoked by target '{target}' does not exist.")

    # validate that the number of args passed into each recipe invocation matches the number of args in the recipe
    for target, exec in data.execution_index.items():
        if "recipe" in exec:
            for executable in exec["recipe"]:
                if isinstance(executable, RecipeInvocation):
                    recipe = data.recipe_index[executable.name]
                    if len(executable.args) != len(recipe.parameters):
                        raise Exception(
                            f"Recipe '{executable.name}' invoked by target '{target}' has {len(recipe.parameters)} args but was invoked with {len(executable.args)} args."
                        )

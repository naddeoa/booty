# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false
from typing import Dict, Iterator, List, Sequence, Union, overload
from lark import ParseTree, Token, Tree


from booty.types import Executable, RecipeDefinition, RecipeInvocation, ShellCommand, TargetNames, compact_shell_executables


def get_target_names(ast: ParseTree) -> List[str]:
    results = list(ast.find_pred(lambda x: x.data == "target_name"))
    targets = [str(it.children[0]) for it in results]
    return targets


DependencyIndex = Dict[TargetNames, List[TargetNames]]

ExecutableIndex = Dict[TargetNames, Dict[str, List[Executable]]]


def find_tokens(ast: ParseTree, token_name: str) -> Sequence[Token]:
    return list(ast.scan_values(lambda it: isinstance(it, Token) and it.type == token_name))


def find_token(ast: ParseTree, token_name: str) -> Token:
    result = find_tokens(ast, token_name)
    if len(result) == 0:
        raise Exception(f"Couldn't find token {token_name}")

    if len(result) > 1:
        raise Exception(f"Exepcted a single {token_name} token, but found {len(result)}: {result}")

    return result[0]


def find_token_value(ast: ParseTree, token_name: str) -> str:
    return find_token(ast, token_name).value


def find_token_values(ast: ParseTree, token_name: str) -> Sequence[str]:
    return [it.value for it in find_tokens(ast, token_name)]


def get_dependencies(ast: ParseTree, executable_index: ExecutableIndex) -> DependencyIndex:
    depends_on = list(ast.find_pred(lambda x: x.data == "depends_on"))
    deppended_upon = list(ast.find_pred(lambda x: x.data == "depended_upon"))
    dependencies: Dict[str, List[str]] = {target: [] for target in executable_index.keys()}
    for it in depends_on:
        target_name = str(it.children[0])
        dependencies[target_name] = dependencies.get(target_name, None) or []
        for dep in it.children[1:]:
            dependencies[target_name].append(str(dep))

    for it in deppended_upon:
        target_name = str(it.children[0])

        dependencies[target_name] = dependencies.get(target_name, None) or []
        for dep in it.children[1:]:
            dependencies[str(dep)] = dependencies.get(str(dep), None) or []
            dependencies[str(dep)].append(target_name)

    return dependencies


def get_zero_dependency_targets(dependencies: DependencyIndex) -> List[str]:
    return [k for k, v in dependencies.items() if len(v) == 0]


@overload
def str_value(_tree: Tree[Token]) -> str:
    ...


@overload
def str_value(_tree: Iterator[Tree[Token]]) -> str:
    ...


def str_value(tree: Union[Tree[Token], Iterator[Tree[Token]]]) -> str:
    if isinstance(tree, Tree):
        return tree.children[0].value  # type: ignore[reportUnknownMemberType]
    else:
        return next(tree).children[0].value  # type: ignore[reportUnknownMemberType]


def get_executable_index(ast: ParseTree) -> ExecutableIndex:
    """
    Get a dictionary of target names to a dictionary of recipe methods to executables.
    For example:

    {
        "pyenv": {
            "setup": [ShellCommand("apt install ..."), RecipeInvocation("curl", ["https://pyenv.run", "|", "bash"])],
            "is_setup": [ShellCommand("which pyenv")]
        },
        "pipx": {
            "recipe": [RecipeInvocation("apt", ["install", "pipx"])]
        }
    }

    The pipx target is just a recipe invocation. The parser enforces that it will only have a single RecipeInvocation in that case.
    """

    executables: Dict[str, Dict[str, List[Executable]]] = {}
    targets = list(ast.find_pred(lambda x: x.data == "target"))
    for target in targets:
        target_name = str_value(target.find_data("target_name"))
        executables[target_name] = executables.get(target_name, None) or {}

        # targets can have either def or recipe invocation as direct children
        for definition in target.find_data("def"):
            for single_or_multi_def in definition.find_pred(lambda node: node.data == "single_line_def" or node.data == "multi_line_def"):
                implements = find_token_value(single_or_multi_def, "IMPLEMENTS_NAME").strip()
                executables[target_name][implements] = executables[target_name].get(implements, None) or []

                for shell_or_recipe in single_or_multi_def.find_pred(
                    lambda node: node.data == "recipe_invocation" or node.data == "shell_line"
                ):
                    if isinstance(shell_or_recipe, Token):
                        raise Exception("This should be impossible")

                    recipe_parameters = list(shell_or_recipe.find_data("recipe_parameter_list"))
                    shell_lines = find_token_values(shell_or_recipe, "SHELL_LINE")

                    if len(recipe_parameters) > 0 and len(shell_lines) > 0:
                        raise Exception(
                            f"This should be impossible, they're mutually exclusive in the grammar: {recipe_parameters}\n{shell_lines}"
                        )

                    if len(shell_lines) > 0:
                        cmd = "\n".join([it for it in shell_lines])
                        shell_command = ShellCommand(cmd)
                        executables[target_name][implements].append(shell_command)
                    else:
                        recipe_name = find_token_value(single_or_multi_def, "NAME")

                        args: Sequence[Sequence[str]] = []
                        for parameter in recipe_parameters:
                            args.append(find_token_values(parameter, "INVOCATION_ARGS"))

                        recipe_invocation = RecipeInvocation(recipe_name, args)
                        executables[target_name][implements].append(recipe_invocation)

        # targets that just call a recipe, they don't define their logic inline
        for recipe_invocation in target.find_data("recipe_invocation"):
            if target_name in executables and len(executables[target_name]) != 0:
                # What's a nice way of making sure I'm looking only at recipe_invocations that are not part of a def?
                continue

            recipe_name = str(recipe_invocation.children[0])

            recipe_parameter = recipe_invocation.find_data("recipe_parameter")
            args: Sequence[Sequence[str]] = []
            for parameter in recipe_parameter:
                args.append(find_token_values(parameter, "INVOCATION_ARGS"))

            recipe_invocation = RecipeInvocation(recipe_name, args)
            executables[target_name]["recipe"] = executables[target_name].get("recipe", None) or []
            executables[target_name]["recipe"].append(recipe_invocation)

    # compact the shell commands
    for target_name, target_definition in executables.items():
        for def_name, execs in target_definition.items():
            target_definition[def_name] = compact_shell_executables(execs)

    return executables


RecipeDefinitionIndex = Dict[str, RecipeDefinition]


def get_recipe_definition_index(ast: ParseTree) -> RecipeDefinitionIndex:
    recipe_definitions: Dict[str, RecipeDefinition] = {}
    recipes = list(ast.find_pred(lambda x: x.data == "recipe"))
    for recipe in recipes:
        recipe_name = find_token_value(recipe, "RECIPE_NAME")
        recipe_definitions[recipe_name] = recipe_definitions.get(recipe_name, None) or RecipeDefinition(recipe_name)

        recipe_arguments = find_token_values(recipe, "ARGUMENT_NAME")
        recipe_definitions[recipe_name].parameters = recipe_arguments
        # recipe_definitions[recipe_name].parameters = [str(arg.children[0].value) for arg in list(recipe.find_data("arguments"))]

        for single_or_multi_def in list(recipe.find_pred(lambda it: it.data == "single_line_def" or it.data == "multi_line_def")):
            implements = find_token_value(single_or_multi_def, "IMPLEMENTS_NAME").strip()

            recipe_definitions[recipe_name].defs[implements] = recipe_definitions[recipe_name].defs.get(implements, None) or []
            for shell_or_recipe in single_or_multi_def.find_pred(
                lambda node: node.data == "recipe_invocation" or node.data == "shell_line"
            ):
                if isinstance(shell_or_recipe, Token):
                    raise Exception("This should be impossible")

                recipe_parameters = list(shell_or_recipe.find_data("recipe_parameter_list"))
                shell_lines = find_token_values(shell_or_recipe, "SHELL_LINE")

                if len(recipe_parameters) > 0 and len(shell_lines) > 0:
                    raise Exception(
                        f"This should be impossible, they're mutually exclusive in the grammar: {recipe_parameters}\n{shell_lines}"
                    )

                if len(shell_lines) > 0:
                    cmd = "\n".join([it for it in shell_lines])
                    shell_command = ShellCommand(cmd)
                    recipe_definitions[recipe_name].defs[implements].append(shell_command)
                else:
                    # Not the name of the current recipe, but the name of the recipe being called.
                    recipe_call_name = find_token_value(single_or_multi_def, "NAME")

                    args: Sequence[Sequence[str]] = []
                    for parameter in recipe_parameters:
                        args.append(find_token_values(parameter, "INVOCATION_ARGS"))

                    recipe_invocation = RecipeInvocation(recipe_call_name, args)
                    recipe_definitions[recipe_name].defs[implements].append(recipe_invocation)

    # compact the shell commands
    for recipe_name, recipe_definition in recipe_definitions.items():
        for def_name, executables in recipe_definition.defs.items():
            recipe_definition.defs[def_name] = compact_shell_executables(executables)

    return recipe_definitions

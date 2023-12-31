from collections.abc import Generator
from dataclasses import dataclass, field
import re
from typing import Dict, List, Literal, Sequence, Union


@dataclass
class ShellCommand:
    command: str


@dataclass
class RecipeInvocation:
    name: str
    args: Sequence[Sequence[str]]


Executable = Union[RecipeInvocation, ShellCommand]


@dataclass
class TargetDefinition:
    target_name: str
    definition: Union[Dict[str, List[Executable]], RecipeInvocation]

    # TODO put a bunch of stuff in here that I've been putting into types.py, execute.py, and app.py


TargetNames = str


def compact_shell_executables(executables: List[Executable]) -> List[Executable]:
    """
    Reduce all contiguous ShellCommands into a single ShellCommand.

    For example, if the list is [RecipeInvocation, ShellCommand, ShellCommand,  RecipeInvocation] then
    this function will return [RecipeInvocation, ShellCommand, RecipeInvocation]

    ShellCommands are reduced by simple string concatenation with newlines.
    """
    compacted_executables: List[Executable] = []
    for executable in executables:
        if isinstance(executable, RecipeInvocation):
            compacted_executables.append(executable)
        else:
            if len(compacted_executables) == 0 or isinstance(compacted_executables[-1], RecipeInvocation):
                first_cmd = ShellCommand(executable.command.strip())
                compacted_executables.append(first_cmd)
            else:
                compacted_executables[-1].command += "\n" + executable.command.strip()

    return compacted_executables


@dataclass
class RecipeDefinition:
    name: str
    defs: Dict[str, List[Executable]] = field(default_factory=dict)
    parameters: Sequence[str] = field(default_factory=list)

    def get_setup_commands(self, args: Sequence[Sequence[str]], recipes: Dict[str, "RecipeDefinition"]) -> List[str]:
        return list(self.iter_commands(args, self.defs["setup"], recipes, method="setup"))

    def get_is_setup_commands(self, args: Sequence[Sequence[str]], recipes: Dict[str, "RecipeDefinition"]) -> List[str]:
        return list(self.iter_commands(args, self.defs["is_setup"], recipes, method="is_setup"))

    def iter_commands(
        self,
        args: Sequence[Sequence[str]],
        executables: List[Executable],
        recipes: Dict[str, "RecipeDefinition"],
        method: Literal["setup", "is_setup"],
    ) -> Generator[str, None, None]:
        for executable in executables:
            if isinstance(executable, ShellCommand):
                # Substitute the arguments into the shell command by replacing $(( ... )) with the argument.
                command = executable.command
                final_command = self._substitute_arg_values(command, self.parameters, args)
                yield final_command
            else:
                # this path ends up happening when executing a recipe that calls another recipe.
                recipe = recipes[executable.name]
                yield from recipe.iter_commands(executable.args, recipe.defs[method], recipes, method=method)

    def _substitute_arg_values(self, command: str, arg_names: Sequence[str], args: Sequence[Sequence[str]]) -> str:
        """
        Commands can reference variables by using $(( ... )) syntax. If a command has $(( arg1 )) then
        and arg1 is the first argument in args_names, then the first value in args will be substituted
        into the command.
        """

        arg_values = [" ".join(it) for it in args]

        for i, arg_name in enumerate(arg_names):
            # Create a regex pattern that allows for optional whitespace
            pattern = r"\$\(\(\s*" + re.escape(arg_name) + r"\s*\)\)"

            # Use re.sub() for replacement
            command = re.sub(pattern, arg_values[i], command)

        return command

from dataclasses import dataclass, field
import re
import subprocess
from typing import Dict, List, Sequence, Union


@dataclass
class ShellCommand:
    command: str

    def execute(self) -> None:
        subprocess.run(["bash", "-c", self.command])


@dataclass
class RecipeInvocation:
    name: str
    args: Sequence[Sequence[str]]


Executable = Union[RecipeInvocation, ShellCommand]

TargetDefinition = Union[Dict[str, List[Executable]], RecipeInvocation]


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
                compacted_executables.append(executable)
            else:
                compacted_executables[-1].command += "\n" + executable.command

    return compacted_executables


@dataclass
class RecipeDefinition:
    name: str
    defs: Dict[str, List[Executable]] = field(default_factory=dict)
    parameters: Sequence[str] = field(default_factory=list)

    def setup(self, args: Sequence[Sequence[str]], recipes: Dict[str, "RecipeDefinition"]) -> None:
        """
        Execute the setup method of the recipe.
        """
        setup = self.defs["setup"]
        for executable in setup:
            if isinstance(executable, ShellCommand):
                # Substitute the arguments into the shell command by replacing $(( ... )) with the argument.
                command = executable.command
                final_command = self._substitute_arg_values(command, self.parameters, args)
                subprocess.run(final_command, shell=True)

            else:
                recipe = recipes[executable.name]
                recipe.setup(executable.args, recipes)

    def is_setup(self, args: Sequence[Sequence[str]], recipes: Dict[str, "RecipeDefinition"]) -> bool:
        """
        Check if the recipe is setup.
        """
        print()
        print('==========================')
        print(f"Executing is_setup for {self.name} with args {args}")

        # next up, string templating with the def/parameters, assuming the order of parameters matches the order of args

        is_setup = self.defs["is_setup"]

        failures = False
        for executable in is_setup:
            if isinstance(executable, ShellCommand):
                # Substitute the arguments into the shell command by replacing $(( ... )) with the argument.
                command = executable.command
                final_command = self._substitute_arg_values(command, self.parameters, args)
                print(f"Executing command: {final_command}")

                result = subprocess.run(["bash", "-c", final_command], shell=False)
                if result.returncode == 0:
                    failures = True

            else:
                recipe = recipes[executable.name]
                return recipe.is_setup(executable.args, recipes)

        print('==========================')
        print()
        return failures

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

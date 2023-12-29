from dataclasses import dataclass, field
import time
from pprint import pprint
from typing import Any, Dict, Generator, List, Literal, cast

from booty.ast_util import get_dependencies, get_executable_index, get_recipe_definition_index
from booty.execute import BootyData, check_target_status, install_target
from booty.graph import DependencyGraph
from booty.parser import parse
from booty.target_logger import TargetLogger
from booty.types import Executable, RecipeInvocation
from booty.validation import validate
from booty.lang.stdlib import stdlib

from progress_table import ProgressTable

# Monkeypatch SymbolsUnicodeBare.embedded_pbar_filled to be -
# SymbolsUnicodeBare.embedded_pbar_filled = "─"


@dataclass
class StatusResult:
    missing: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    installed: List[str] = field(default_factory=list)
    total_time: float = 0.0


class App:
    def __init__(self, config_path: str, logger: TargetLogger, debug: bool = False) -> None:
        self.config_path = config_path
        self.data = self.setup(debug)
        self.logger = logger

    def setup(self, debug: bool) -> BootyData:
        """
        Parse the config file and create all of the indexes that we'll need to execute the booty.
        Also runs validation.
        """
        with open(self.config_path) as f:
            config = f.read()

        ast = parse(config)
        if debug:
            print("AST:")
            print(ast.pretty())
        stdlib_ast = parse(stdlib)
        executables = get_executable_index(ast)
        if debug:
            print("Executables:")
            pprint(executables)
        dependencies = get_dependencies(ast, executables)
        if debug:
            print("Dependencies:")
            pprint(dependencies)
        G = DependencyGraph.from_index(dependencies)
        recipes = get_recipe_definition_index(ast)
        if debug:
            print("Recipes:")
            pprint(recipes)
        std_recipes = get_recipe_definition_index(stdlib_ast)
        all_recipes = {**std_recipes, **recipes}  # Make the user recipes overwrite the stdlib ones
        conf = BootyData(execution_index=executables, recipe_index=all_recipes, G=G, ast=ast, dependency_index=dependencies)
        validate(conf)
        return conf

    def status(self) -> StatusResult:
        """
        List the install status of each target
        """
        largest_target_name = max([len(t) for t in self.data.execution_index.keys()])
        dependency_strings: Dict[str, str] = {
            target: ", ".join(deps) if deps else "-" for target, deps in self.data.dependency_index.items()
        }
        largest_dependency_name = max([len(t) for t in dependency_strings.values()])

        table = ProgressTable(
            default_column_alignment="left",
            table_style="bare",
            embedded_progress_bar=True,
            refresh_rate=100,
            reprint_header_every_n_rows=60,
        )
        table.add_column("target", width=largest_target_name + 2)  # type: ignore[reportUnknownMemberType]
        table.add_column("dependencies", width=largest_dependency_name + 2)  # type: ignore[reportUnknownMemberType]
        table.add_column("status", width=15)  # type: ignore[reportUnknownMemberType]
        table.add_column("details", width=70)  # type: ignore[reportUnknownMemberType]
        table.add_column("time", alignment="right", width=15)  # type: ignore[reportUnknownMemberType]

        print("Getting target status:")
        prog: Generator[str, Any, None] = cast(Generator[str, Any, None], table(list(self.data.G.iterator())))
        status_result = StatusResult()
        total_time = 0.0
        for target in prog:
            deps_string = dependency_strings[target]
            table["target"] = target
            table["dependencies"] = deps_string

            exec = self.data.execution_index[target]
            time.sleep(0.01)
            table["status"] = "🟡 Checking..."
            time.sleep(0.01)
            table["details"] = self._display_is_setup(exec)
            time.sleep(0.01)

            start_time = time.perf_counter()
            result = check_target_status(self.data, target)
            _time = time.perf_counter() - start_time
            total_time += _time
            table["time"] = f"{_time:.2f}s"

            if result is None:
                table["status"] = "🟢 Installed"
                status_result.installed.append(target)
            else:
                if result.returncode == 1:
                    table["status"] = "🟡 Not installed"
                    table["details"] = result.stdout if result.stdout else table["details"]
                    status_result.missing.append(target)
                    self.logger.log_is_setup(target, result.stdout, result.stderr)
                else:
                    # TODO send PR to library to fix the formatting with unicode/emoji. Length is wrong.
                    table["status"] = "🔴 Error"
                    table["details"] = result.stderr.strip()
                    status_result.errors.append(target)
                    self.logger.log_is_setup(target, result.stdout, result.stderr)

            table.next_row()

        table.close()
        status_result.total_time = total_time
        return status_result

    def install_missing(self, status_result: StatusResult) -> StatusResult:
        """
        Install all missing targets and attempt to install the ones that failed status check.
        """
        largest_target_name = max([len(t) for t in [*status_result.missing, *status_result.errors]])

        table = ProgressTable(
            default_column_alignment="left",
            table_style="bare",
            embedded_progress_bar=True,
            refresh_rate=100,
            reprint_header_every_n_rows=60,
        )
        table.add_column("target", width=largest_target_name + 2)  # type: ignore[reportUnknownMemberType]
        table.add_column("status", width=15)  # type: ignore[reportUnknownMemberType]
        table.add_column("details", width=100)  # type: ignore[reportUnknownMemberType]
        table.add_column("time", alignment="right", width=15)  # type: ignore[reportUnknownMemberType]
        missing_packages = set([*status_result.missing, *status_result.errors])

        prog: Generator[str, Any, None] = cast(Generator[str, Any, None], table(len(self.data.G.dependencies.keys())))

        print("Installing targets:")

        total_time = 0.0
        status_result = StatusResult()
        gen = self.data.G.bfs()
        try:
            next(prog)
            next(gen)  # Skip the first fake target
            target = gen.send(True)

            while True:
                if target not in missing_packages:
                    target = gen.send(True)
                    continue

                table["target"] = target
                exec = self.data.execution_index[target]

                time.sleep(0.01)
                table["status"] = "🟡 Installing..."
                time.sleep(0.01)
                table["details"] = self._display_setup(exec)
                time.sleep(0.01)

                start_time = time.perf_counter()
                result = install_target(self.data, target)
                _time = time.perf_counter() - start_time
                total_time += _time
                table["time"] = f"{_time:.2f}s"

                if result is None:
                    table["status"] = "🟢 Installed"
                    status_result.installed.append(target)
                else:
                    table["status"] = "🔴 Error"
                    table["details"] = result.stderr.strip().replace("\n", " ")
                    self.logger.log_setup(target, result.stdout, result.stderr)
                    status_result.errors.append(target)
                table.next_row()

                target = gen.send(result is None)

        except StopIteration as e:
            skipped: List[str] = e.value

        for target in skipped:
            table["target"] = target
            table["status"] = "🟡 Skipped"
            table["details"] = "Dependency failure"
            table.next_row()

        table.close()

        print()
        print()
        print("Install Report:")
        print()
        print(f"🟢 ({len(status_result.installed)}) targets installed")
        print(f"🟡 ({len(skipped)}) targets skipped because of dependency failures")
        print(f"🔴 ({len(status_result.errors)}) targets failed because of errors")

        print()
        print(f"🕒 Total time: {total_time:.2f}s")
        print()
        print()
        return status_result

    def _display(self, it: Dict[str, List[Executable]], method: Literal["setup", "is_setup"]) -> str:
        exec = it[method] if method in it else it["recipe"]

        commands: List[str] = []
        for executable in exec:
            if isinstance(executable, RecipeInvocation):
                recipe = self.data.recipe_index[executable.name]
                if method == "setup":
                    commands.append("\n".join(recipe.get_setup_commands(executable.args, self.data.recipe_index)))
                else:
                    commands.append("\n".join(recipe.get_is_setup_commands(executable.args, self.data.recipe_index)))
            else:
                commands.append(executable.command)

        # what's the best way to display multiple commands? They're bound to be too long. For now
        # I'll just show the first one and maybe append a "..." if there are more.
        has_multiple_commands = len(commands) > 1 or "\n" in commands[0]
        first_command = commands[0].strip().replace("\n", "\\n")[:60]
        return f"{first_command}{'...' if has_multiple_commands else ''}"

    def _display_is_setup(self, it: Dict[str, List[Executable]]) -> str:
        return self._display(it, method="is_setup")

    def _display_setup(self, it: Dict[str, List[Executable]]) -> str:
        return self._display(it, method="setup")

from dataclasses import dataclass, field
import time
from pprint import pprint
from typing import Dict, List, Literal

from rich.box import SIMPLE
from rich.text import Text
from rich.table import Table
from rich.console import Group
from rich.live import Live
from rich.progress import Progress

from booty.ast_util import get_dependencies, get_executable_index, get_recipe_definition_index
from booty.execute import BootyData, check_target_status, install_target
from booty.graph import DependencyGraph
from booty.parser import parse
from booty.target_logger import TargetLogger
from booty.types import Executable, RecipeInvocation
from booty.validation import validate
from booty.lang.stdlib import stdlib


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

        table = Table(title="Target Status", show_header=True, show_edge=False, title_style="bold", box=SIMPLE)

        table.add_column("Target", no_wrap=True, width=max(largest_target_name + 2, 6))
        table.add_column("Dependencies", width=max(largest_dependency_name + 2, 12))
        table.add_column("Status", width=20)
        table.add_column("Details", width=70)
        table.add_column("Time", justify="right", width=15)

        overall_progress = Progress()
        overall_id = overall_progress.add_task("Status", total=len(self.data.G.dependencies.keys()))

        status_result = StatusResult()
        total_time = 0.0

        group = Group(table, overall_progress)
        with Live(group, refresh_per_second=10):
            for target in self.data.G.iterator():
                deps_string = dependency_strings[target]

                target_text = Text(target)
                dependency_text = Text(deps_string)
                status_text = Text("🟡 Checking...")
                details_text = Text(self._display_is_setup(self.data.execution_index[target]))
                time_text = Text("")  # Make update in real time

                table.add_row(target_text, dependency_text, status_text, details_text, time_text)

                start_time = time.perf_counter()
                result = check_target_status(self.data, target)
                _time = time.perf_counter() - start_time
                total_time += _time
                time_text.plain = f"{_time:.2f}s"

                if result is None:
                    status_result.installed.append(target)
                    status_text.plain = "🟢 Installed"
                else:
                    if result.returncode == 1:
                        status_result.missing.append(target)
                        status_text.plain = "🟡 Not installed"
                        details_text.plain = result.stdout if result.stdout else details_text.plain
                        self.logger.log_is_setup(target, result.stdout, result.stderr)
                    else:
                        status_result.errors.append(target)
                        status_text.plain = "🔴 Error"
                        details_text.plain = result.stderr.strip()
                        self.logger.log_is_setup(target, result.stdout, result.stderr)

                overall_progress.advance(overall_id)

            overall_progress.update(overall_id, completed=True)
            overall_progress.update(overall_id, visible=False)
        status_result.total_time = total_time
        return status_result

    def install_missing(self, status_result: StatusResult) -> StatusResult:
        """
        Install all missing targets and attempt to install the ones that failed status check.
        """
        largest_target_name = max([len(t) for t in [*status_result.missing, *status_result.errors]])

        table = Table(title="Install Status", show_header=True, show_edge=False, title_style="bold", box=SIMPLE)
        table.add_column("Target", no_wrap=True, width=largest_target_name + 2)
        table.add_column("Status", width=20)
        table.add_column("Details", width=70)
        table.add_column("Time", justify="right", width=20)

        overall_progress = Progress()
        overall_id = overall_progress.add_task("Status", total=len(self.data.G.dependencies.keys()))
        missing_packages = set([*status_result.missing, *status_result.errors])

        group = Group(table, overall_progress)

        total_time = 0.0
        status_result = StatusResult()
        gen = self.data.G.bfs()
        with Live(group, refresh_per_second=10):
            try:
                next(gen)  # Skip the first fake target
                target = gen.send(True)

                while True:
                    if target not in missing_packages:
                        target = gen.send(True)
                        continue

                    target_text = Text(target)
                    status_text = Text("🟡 Installing...")
                    details_text = Text(self._display_setup(self.data.execution_index[target]))
                    time_text = Text("")  # Make update in real time
                    table.add_row(target_text, status_text, details_text, time_text)

                    target_text.plain = target

                    details_text.plain = self._display_setup(self.data.execution_index[target])

                    start_time = time.perf_counter()
                    result = install_target(self.data, target)
                    _time = time.perf_counter() - start_time
                    total_time += _time
                    time_text.plain = f"{_time:.2f}s"

                    if result is None:
                        status_result.installed.append(target)
                        status_text.plain = "🟢 Installed"
                    else:
                        status_text.plain = "🔴 Error"
                        details_text.plain = result.stderr.strip().replace("\n", " ")
                        self.logger.log_setup(target, result.stdout, result.stderr)
                        status_result.errors.append(target)

                    target = gen.send(result is None)
                    overall_progress.advance(overall_id)

            except StopIteration as e:
                skipped: List[str] = e.value

            for target in skipped:
                target_text = Text(target)
                status_text = Text("🟡 Skipped")
                details_text = Text("Dependency failure")
                time_text = Text("")
                table.add_row(target_text, status_text, details_text, time_text)

            overall_progress.update(overall_id, completed=True)
            overall_progress.update(overall_id, visible=False)

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

from dataclasses import dataclass, field
import time
import subprocess
from pprint import pprint
from typing import Dict, List, Literal

from rich.box import SIMPLE
from rich.text import Text
from rich.padding import Padding
from rich.table import Table
from rich.console import Group
from rich.live import Live
from rich.progress import Progress

from booty.ast_util import get_dependencies, get_executable_index, get_recipe_definition_index
from booty.execute import BootyData, CommandExecutor, get_commands
from booty.graph import DependencyGraph
from booty.lang import get_stdlib
from booty.parser import parse
from booty.target_logger import TargetLogger
from booty.types import Executable, RecipeInvocation
from booty.ui import Padder, StdTree, UpdateTracker
from booty.validation import validate


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
        stdlib_ast = parse(get_stdlib())
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

    def check_sudo_usage(self) -> None:
        sudo_targets: List[str] = []

        for target, commands in get_commands(self.data, "is_setup").items():
            for cmd in commands:
                if "sudo" in cmd:
                    sudo_targets.append(target)

        for target, commands in get_commands(self.data, "setup").items():
            for cmd in commands:
                if "sudo" in cmd:
                    sudo_targets.append(target)

        if sudo_targets:
            # run sudo -v to make sure the user has sudo access
            targets = ", ".join(set(sudo_targets))
            print(
                f"""
Detected sudo in targets: '{targets}'.
Running `sudo -v` to cache sudo credentials. You can disable this behavior with `booty --no-sudo`. See `booty --help` for details.
""",
                flush=True,
            )
            subprocess.run(["sudo", "-v"], check=True)

    def status(self) -> StatusResult:
        """
        List the install status of each target
        """
        dependency_strings: Dict[str, str] = {
            target: ", ".join(deps) if deps else "-" for target, deps in self.data.dependency_index.items()
        }

        table = Table(title="Target Status", show_header=True, show_edge=False, title_style="bold", box=SIMPLE)
        table.add_column("Target", no_wrap=True, width=20)
        table.add_column("Dependencies", width=20, no_wrap=True)
        table.add_column("Status", width=20, no_wrap=True)
        table.add_column("Details", width=70, no_wrap=True)
        table.add_column("Time", justify="right", width=10)

        overall_progress = Progress()
        overall_id = overall_progress.add_task("Status", total=len(self.data.G.dependencies.keys()))

        status_result = StatusResult()
        total_time = 0.0

        padder = Padder()
        padding = Padding(table, (0, 0, 0, 0))
        group = Group(padding, overall_progress)

        with Live(auto_refresh=False) as live:
            for target in self.data.G.iterator():
                deps_string = dependency_strings[target]

                target_text = Text(target)
                dependency_text = Text(deps_string)
                status_text = Text("🟡 Checking...")

                tree = StdTree(self._display_is_setup(self.data.execution_index[target]))

                time_text = Text("")  # Make update in real time

                table.add_row(target_text, dependency_text, status_text, tree.tree, time_text)

                start_time = time.perf_counter()
                cmd = CommandExecutor(self.data, target, "is_setup")
                for _ in cmd.execute():
                    time_text.plain = f"{time.perf_counter() - start_time:.2f}s"
                    tree.set_stdout(cmd.latest_stdout())
                    tree.set_stderr(cmd.latest_stderr())
                    padding.bottom = padder.get_padding(tree)
                    live.update(group, refresh=True)

                target_time = time.perf_counter() - start_time
                total_time += target_time
                time_text.plain = f"{target_time:.2f}s"

                if cmd.code == 0:
                    status_result.installed.append(target)
                    status_text.plain = "🟢 Installed"
                    tree.reset()
                else:
                    tree.set_stdout(cmd.latest_stdout())
                    tree.set_stderr(cmd.latest_stderr())

                    if cmd.code == 1:
                        status_result.missing.append(target)
                        status_text.plain = "🟡 Not installed"
                        self.logger.log_is_setup(target, cmd.all_stdout(), cmd.all_stderr())
                    else:
                        status_result.errors.append(target)
                        status_text.plain = "🔴 Error"
                        self.logger.log_is_setup(target, cmd.all_stdout(), cmd.all_stderr())

                overall_progress.advance(overall_id)
                live.update(group, refresh=True)

            overall_progress.update(overall_id, completed=True)
            overall_progress.update(overall_id, visible=False)
        status_result.total_time = total_time
        return status_result

    def install_missing(self, status_result: StatusResult) -> StatusResult:
        """
        Install all missing targets and attempt to install the ones that failed status check.
        """

        table = Table(title="Setup Status", show_header=True, show_edge=False, title_style="bold", box=SIMPLE)
        table.add_column("Target", no_wrap=True, width=20)
        table.add_column("Status", width=20, no_wrap=True)
        table.add_column("Details", width=93, no_wrap=True)
        table.add_column("Time", justify="right", width=10, no_wrap=True)

        missing_packages = set([*status_result.missing, *status_result.errors])
        overall_progress = Progress()
        overall_id = overall_progress.add_task("Status", total=len(missing_packages))

        padder = Padder()
        padding = Padding(table, (0, 0, 0, 0))
        group = Group(padding, overall_progress)

        total_time = 0.0
        status_result = StatusResult()
        gen = self.data.G.bfs()
        tracker = UpdateTracker()
        with Live(auto_refresh=False) as live:
            try:
                next(gen)  # Skip the first fake target
                target = gen.send(True)

                while True:
                    if target not in missing_packages:
                        target = gen.send(True)
                        continue

                    target_text = Text(target)
                    status_text = Text("🟡 Installing...")

                    tree = StdTree(self._display_setup(self.data.execution_index[target]))
                    time_text = Text("")  # Make update in real time
                    table.add_row(target_text, status_text, tree.tree, time_text)
                    target_text.plain = target
                    start_time = time.perf_counter()

                    cmd = CommandExecutor(self.data, target, "setup")
                    for _ in cmd.execute():
                        time_fmt = f"{time.perf_counter() - start_time:.2f}s"
                        stdout = cmd.latest_stdout()
                        stderr = cmd.latest_stderr()
                        time_text.plain = time_fmt

                        tree.set_stdout(stdout)
                        tree.set_stderr(stderr)
                        padding.bottom = padder.get_padding(tree)

                        tracker.update(lambda: live.update(group, refresh=True), [target, stdout, stderr])

                    cmd_time = time.perf_counter() - start_time
                    time_text.plain = f"{cmd_time:.2f}s"
                    total_time += cmd_time

                    if cmd.code == 0:
                        status_result.installed.append(target)
                        status_text.plain = "🟢 Installed"
                        tree.reset()
                        padding.bottom = padder.get_padding(tree)
                    else:
                        status_text.plain = "🔴 Error"
                        self.logger.log_setup(target, cmd.all_stdout(), cmd.all_stderr())
                        status_result.errors.append(target)

                    target = gen.send(cmd.code == 0)
                    overall_progress.advance(overall_id)
                    live.update(group, refresh=True)

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
                    cmds = [it.replace("\n", "\\n ") for it in recipe.get_setup_commands(executable.args, self.data.recipe_index)]
                    commands.append("\\n".join(cmds))
                else:
                    cmds = [it.replace("\n", "\\n ") for it in recipe.get_is_setup_commands(executable.args, self.data.recipe_index)]
                    commands.append("\\n ".join(cmds))
            else:
                commands.append(executable.command.replace("\n", "\\n"))

        return "\\n ".join(commands[:3])

    def _display_is_setup(self, it: Dict[str, List[Executable]]) -> str:
        return self._display(it, method="is_setup")

    def _display_setup(self, it: Dict[str, List[Executable]]) -> str:
        return self._display(it, method="setup")

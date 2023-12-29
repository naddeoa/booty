from dataclasses import dataclass
from typing import Dict, Generator, Iterator, List, Sequence, Set, TypeVar

from booty.ast_util import DependencyIndex

T = TypeVar("T")


@dataclass(frozen=True)
class Dependency:
    value: str
    children: Sequence[str]

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Dependency):
            return NotImplemented

        return self.value == other.value


@dataclass
class DependencyBuilder:
    value: str
    children: List[str]

    def to_dependency(self) -> Dependency:
        return Dependency(self.value, [child for child in self.children])


# This is the root of the graph. Every target that doesn't have any dependencies
# will depend on this node and the graph search will start from this node.
StartNode = "__START__"


@dataclass
class DependencyGraph:
    start: Dependency
    dependencies: Dict[str, Dependency]

    @classmethod
    def from_index(cls, dependencies: DependencyIndex) -> "DependencyGraph":
        builder = DependencyGraphBuilder(StartNode)

        for package, deps in dependencies.items():
            if not deps:
                builder.add_dependency(package, StartNode)
            else:
                for dep in deps:
                    builder.add_dependency(package, dep)

        return builder.build()

    def bfs(self) -> Generator[str, bool, Sequence[str]]:
        to_visit: List[Dependency] = [self.start]
        visited: Set[str] = set()
        to_skip: Set[str] = set()
        skipped_nodes: Set[str] = set()

        while to_visit:
            current = to_visit.pop(0)

            # If current has any failed parents then skip it
            if current.value in to_skip:
                skipped_nodes.add(current.value)
                to_skip.update(current.children)
                continue

            if current.value in visited:
                continue
            else:
                success = yield current.value  # Signaled from the generator caller
                visited.add(current.value)

            if not success:
                to_skip.update(current.children)
            else:
                to_visit.extend([self.dependencies[child] for child in current.children if child not in visited])

        all_nodes = set(self.dependencies.keys())
        all_skipped = list(skipped_nodes.union(all_nodes.difference(visited)))
        all_skipped.sort()
        return all_skipped

    def iterator(self, skip_first: bool = True) -> Iterator[str]:
        """
        Iterate over the dependencies in dependency order.
        """
        gen = self.bfs()
        try:
            if skip_first:
                next(gen)
                target = gen.send(True)
            else:
                target = next(gen)

            while True:
                yield target
                target = gen.send(True)
        except StopIteration:
            pass

    def find_first_cycle(self) -> List[str]:
        def _dfs(node: Dependency, visited: Set[str], stack: Dict[str, None]) -> List[str]:
            visited.add(node.value)
            stack[node.value] = None

            for child in node.children:
                if child not in visited:
                    cycle = _dfs(self.dependencies[child], visited, stack)
                    if cycle:
                        return cycle
                elif child in stack:
                    return [*stack.keys(), child]

            del stack[node.value]
            return []

        visited: Set[str] = set()
        stack: Dict[str, None] = {}  # Apparently dicts preserve key ordering so this is a hacky list with fast lookup

        for node in self.dependencies.values():
            if node.value not in visited:
                cycle = _dfs(node, visited, stack)
                if cycle:
                    return cycle

        return []


class DependencyGraphBuilder:
    def __init__(self, start_target: str):
        self.start_target: str = start_target
        self.dependencies: Dict[str, DependencyBuilder] = {start_target: DependencyBuilder(start_target, [])}

    def add_dependency(self, to_target: str, from_target: str) -> "DependencyGraphBuilder":
        if from_target not in self.dependencies:
            self.dependencies[from_target] = DependencyBuilder(from_target, [])

        if to_target not in self.dependencies:
            self.dependencies[to_target] = DependencyBuilder(to_target, [])

        self.dependencies[from_target].children.append(to_target)

        return self

    def build(self) -> DependencyGraph:
        return DependencyGraph(
            self.dependencies[self.start_target].to_dependency(), {k: v.to_dependency() for k, v in self.dependencies.items()}
        )

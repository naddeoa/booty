from dataclasses import dataclass
from typing import Dict, Generator, List, Sequence, Set, TypeVar

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


@dataclass
class DependencyGraph:
    start: Dependency
    dependencies: Dict[str, Dependency]

    def bst(self) -> Generator[Dependency, bool, Sequence[str]]:
        to_visit: List[Dependency] = [self.start]
        visited: Set[str] = set()
        to_skip: Set[str] = set()
        skipped_nodes: Set[str] = set()

        while to_visit:
            current = to_visit.pop(0)
            visited.add(current.value)
            print(f"Visiting {current.value}")

            # If current has any failed parents then skip it
            if current.value in to_skip:
                print(f"Skipping {current.value}")
                skipped_nodes.add(current.value)
                for child in current.children:
                    to_skip.add(child)
                continue

            success = yield current
            print(f"Result: {success}")
            if not success:
                for child in current.children:
                    to_skip.add(child)
            else:
                for child in current.children:
                    if child in visited:
                        continue
                    print(f"Adding {child} to visit")
                    to_visit.append(self.dependencies[child])

        all_nodes = set(self.dependencies.keys())
        all_skipped = list(skipped_nodes.union(all_nodes.difference(visited)))
        all_skipped.sort()
        return all_skipped

    # TODO make this not suck
    def has_cycles(self) -> bool:
        return False


class DependencyGraphBuilder:
    def __init__(self, start_target: str):
        self.start_target: str = start_target
        self.dependencies: Dict[str, DependencyBuilder] = {start_target: DependencyBuilder(start_target, [])}

    def add_dependency(self, from_target: str, to_target: str) -> "DependencyGraphBuilder":
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

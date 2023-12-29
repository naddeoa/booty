from typing import List
from booty.graph import DependencyGraphBuilder


def test_all_success():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("b", "c").add_dependency("c", "d").build()
    gen = graph.bfs()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target)
            target = gen.send(True)
    except StopIteration as e:
        skipped = e.value

    assert graph.start.value == "a"
    assert ["a", "b", "c", "d"] == targets
    assert [] == skipped
    assert graph.find_first_cycle() == []


def test_start_failure():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("b", "c").add_dependency("c", "d").build()
    gen = graph.bfs()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target)
            target = gen.send(False)
    except StopIteration as e:
        skipped = e.value

    assert graph.start.value == "a"
    assert ["a"] == targets
    assert ["b", "c", "d"] == skipped
    assert graph.find_first_cycle() == []


def test_last_failure():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("b", "c").add_dependency("c", "d").build()
    gen = graph.bfs()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target)
            target = gen.send(target != "c")
    except StopIteration as e:
        skipped = e.value

    assert graph.start.value == "a"
    assert ["a", "b", "c"] == targets
    assert ["d"] == skipped
    assert graph.find_first_cycle() == []


def test_wide_graph():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("a", "c").add_dependency("a", "d").build()
    gen = graph.bfs()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target)
            target = gen.send(True)
    except StopIteration as e:
        skipped = e.value
    targets.sort()

    assert graph.start.value == "a"
    assert ["a", "b", "c", "d"] == targets
    assert [] == skipped
    assert graph.find_first_cycle() == []


def test_wide_graph_with_failure():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("a", "c").add_dependency("a", "d").build()
    gen = graph.bfs()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target)
            target = gen.send(target != "c")
    except StopIteration as e:
        skipped = e.value
    targets.sort()

    assert graph.start.value == "a"
    assert ["a", "b", "c", "d"] == targets
    assert [] == skipped
    assert graph.find_first_cycle() == []


def test_wide_graph_with_failure_start():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("a", "c").add_dependency("a", "d").build()
    gen = graph.bfs()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target)
            target = gen.send(False)  # Fail right away
    except StopIteration as e:
        skipped = e.value
    targets.sort()

    assert graph.start.value == "a"
    assert ["a"] == targets
    assert ["b", "c", "d"] == skipped
    assert graph.find_first_cycle() == []


def test_ancestor_failure():
    """
    a is the parent of [b,c], and both c and d are parents of d.
    c will fail which should cause d and e to be skipped, even though d's other parent b was successful.
    f will still run because it has no failed ancestors

         c -- d -- e
        /    /
    -> a -- b -- f

    """
    graph = (
        DependencyGraphBuilder("a")
        .add_dependency("a", "b")
        .add_dependency("a", "c")
        .add_dependency("c", "d")
        .add_dependency("b", "d")
        .add_dependency("b", "f")
        .add_dependency("d", "e")
        .build()
    )
    gen = graph.bfs()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target)
            target = gen.send(target != "c")
    except StopIteration as e:
        skipped = e.value
    targets.sort()
    skipped.sort()

    assert graph.start.value == "a"
    assert ["a", "b", "c", "f"] == targets
    assert ["d", "e"] == skipped
    assert graph.find_first_cycle() == []


def test_ancestor_failure_other_parent():
    """
    a is the parent of [b,c], and both c and d are parents of d.
    c won't fail but b will, which should cause d and e to be skipped.

         c -- d -- e
        /    /
    -> a -- b -- f

    """
    graph = (
        DependencyGraphBuilder("a")
        .add_dependency("a", "b")
        .add_dependency("a", "c")
        .add_dependency("c", "d")
        .add_dependency("b", "d")
        .add_dependency("b", "d")
        .add_dependency("b", "f")
        .add_dependency("d", "e")
        .build()
    )
    gen = graph.bfs()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target)
            target = gen.send(target != "b")
    except StopIteration as e:
        skipped = e.value
    targets.sort()
    skipped.sort()

    assert graph.start.value == "a"
    assert ["a", "b", "c"] == targets
    assert ["d", "e", "f"] == skipped
    assert graph.find_first_cycle() == []


def test_cycle():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("b", "c").add_dependency("c", "a").build()

    assert graph.find_first_cycle() == ["a", "b", "c", "a"]


def test_cycle_deeper():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("b", "c").add_dependency("c", "b").build()

    assert graph.find_first_cycle() == ["a", "b", "c", "b"]


def test_cycle_wide():
    graph = (
        DependencyGraphBuilder("a")
        .add_dependency("a", "b")
        .add_dependency("a", "c")
        .add_dependency("b", "c")
        .add_dependency("c", "b")
        .build()
    )

    assert graph.find_first_cycle() == ["a", "b", "c", "b"]


def test_iterator():
    graph = (
        DependencyGraphBuilder("a")
        .add_dependency("a", "b")
        .add_dependency("a", "c")
        .add_dependency("c", "d")
        .add_dependency("b", "d")
        .add_dependency("b", "d")
        .add_dependency("b", "f")
        .add_dependency("d", "e")
        .build()
    )

    print(list(graph.iterator()))
    assert list(graph.iterator()) == ["a", "b", "c", "d", "f", "e"]


def test_iterator_wide():
    graph = (
        DependencyGraphBuilder("a")
        .add_dependency("a", "b")
        .add_dependency("a", "c")
        .add_dependency("a", "d")
        .add_dependency("d", "e")
        .build()
    )

    print(list(graph.iterator()))
    assert list(graph.iterator()) == ["a", "b", "c", "d", "e"]

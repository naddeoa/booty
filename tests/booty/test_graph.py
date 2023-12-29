from typing import List
from booty.graph import DependencyGraphBuilder


def test_all_success():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("b", "c").add_dependency("c", "d").build()
    gen = graph.bst()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target.value)
            target = gen.send(True)
    except StopIteration as e:
        skipped = e.value

    assert graph.start.value == "a"
    assert ["a", "b", "c", "d"] == targets
    assert [] == skipped
    assert graph.has_cycles() is False


def test_start_failure():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("b", "c").add_dependency("c", "d").build()
    gen = graph.bst()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target.value)
            target = gen.send(False)
    except StopIteration as e:
        skipped = e.value

    assert graph.start.value == "a"
    assert ["a"] == targets
    assert ["b", "c", "d"] == skipped
    assert graph.has_cycles() is False


def test_last_failure():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("b", "c").add_dependency("c", "d").build()
    gen = graph.bst()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target.value)
            target = gen.send(target.value != "c")
    except StopIteration as e:
        skipped = e.value

    assert graph.start.value == "a"
    assert ["a", "b", "c"] == targets
    assert ["d"] == skipped
    assert graph.has_cycles() is False


def test_wide_graph():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("a", "c").add_dependency("a", "d").build()
    gen = graph.bst()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target.value)
            target = gen.send(True)
    except StopIteration as e:
        skipped = e.value
    targets.sort()

    assert graph.start.value == "a"
    assert ["a", "b", "c", "d"] == targets
    assert [] == skipped
    assert graph.has_cycles() is False


def test_wide_graph_with_failure():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("a", "c").add_dependency("a", "d").build()
    gen = graph.bst()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target.value)
            target = gen.send(target.value != "c")
    except StopIteration as e:
        skipped = e.value
    targets.sort()

    assert graph.start.value == "a"
    assert ["a", "b", "c", "d"] == targets
    assert [] == skipped
    assert graph.has_cycles() is False


def test_wide_graph_with_failure_start():
    graph = DependencyGraphBuilder("a").add_dependency("a", "b").add_dependency("a", "c").add_dependency("a", "d").build()
    gen = graph.bst()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target.value)
            target = gen.send(False)  # Fail right away
    except StopIteration as e:
        skipped = e.value
    targets.sort()

    assert graph.start.value == "a"
    assert ["a"] == targets
    assert ["b", "c", "d"] == skipped
    assert graph.has_cycles() is False


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
        .add_dependency("b", "d")
        .add_dependency("b", "f")
        .add_dependency("d", "e")
        .build()
    )
    gen = graph.bst()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target.value)
            target = gen.send(target.value != "c")
    except StopIteration as e:
        skipped = e.value
    targets.sort()
    skipped.sort()

    assert graph.start.value == "a"
    assert ["a", "b", "c", "f"] == targets
    assert ["d", "e"] == skipped
    assert graph.has_cycles() is False

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
    gen = graph.bst()

    targets: List[str] = []
    try:
        target = next(gen)
        while True:
            targets.append(target.value)
            target = gen.send(target.value != "b")
    except StopIteration as e:
        skipped = e.value
    targets.sort()
    skipped.sort()

    assert graph.start.value == "a"
    assert ["a", "b", "c"] == targets
    assert ["d", "e", "f"] == skipped
    assert graph.has_cycles() is False
#
# def test_cycle():
#     graph = (
#         DependencyGraphBuilder("a")
#         .add_dependency("a", "b")
#         .add_dependency("b", "c")
#         .add_dependency("c", "a")
#         .build()
#     )
#
#     assert graph.has_cycles() is True
#
# def test_cycle_deeper():
#     graph = (
#         DependencyGraphBuilder("a")
#         .add_dependency("a", "b")
#         .add_dependency("b", "c")
#         .add_dependency("c", "b")
#         .build()
#     )
#
#     assert graph.has_cycles() is True

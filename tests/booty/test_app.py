from typing import Set
from booty.app import App
from booty.target_logger import TargetLogger


def test_sample_bfs_iterator():
    app = App("examples/install.booty", TargetLogger("./logs"))

    targets: Set[str] = set()
    for target in app.data.G.iterator():
        if target in targets:
            raise Exception(f"Found duplicate target {target}")
        targets.add(target)


def test_sample_bfs_walk():
    app = App("examples/install.booty", TargetLogger("./logs"))

    targets: Set[str] = set()
    gen = app.data.G.bfs()
    try:
        next(gen)  # Skip the first fake target
        target = gen.send(True)
        while True:
            if target in targets:
                raise Exception(f"Found duplicate target {target}")

            targets.add(target)
            target = gen.send(True)
    except StopIteration as e:
        skipped = e.value

    assert skipped == []

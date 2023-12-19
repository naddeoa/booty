from typing import Any, List
import networkx as nx

from booty.ast_util import DependencyIndex

# This is the root of the graph. Every target that doesn't have any dependencies
# will depend on this node and the graph search will start from this node.
StartNode = "__START__"


def get_dependency_graph(dependencies: DependencyIndex) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_node(StartNode)  # type: ignore[reportUnknownMember]

    for package, deps in dependencies.items():
        if not deps:
            G.add_edge(package, StartNode)  # type: ignore[reportUnknownMember]
        else:
            for dep in deps:
                G.add_edge(package, dep)  # type: ignore[reportUnknownMember]

    return G


def has_cycles(G: nx.DiGraph) -> List[Any]:
    return list(nx.simple_cycles(G))  # type: ignore[reportUnknownMember]


def bfs_iterator(G: nx.DiGraph, start_node_name: str = StartNode) -> List[str]:
    bfs_tree = nx.bfs_tree(G, start_node_name, reverse=True)  # type: ignore[reportUnknownMember]
    it = iter(bfs_tree.nodes())  # type: ignore[reportUnknownMember]
    # skip the start node
    next(it)  # type: ignore
    return [str(i) for i in it]  # type: ignore


def dfs_iterator(G: nx.DiGraph, start_node_name: str = StartNode) -> List[str]:
    bfs_tree = nx.dfs_tree(G.reverse(), start_node_name)  # type: ignore[reportUnknownMember]
    it = iter(bfs_tree.nodes())  # type: ignore[reportUnknownMember]
    # skip the start node
    next(it)  # type: ignore
    return [str(i) for i in it]  # type: ignore

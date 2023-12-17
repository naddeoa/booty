from typing import Any, Dict, List
import networkx as nx


def get_dependency_graph(dependencies: Dict[str, List[str]]) -> nx.DiGraph:
    G = nx.DiGraph()
    for package, deps in dependencies.items():
        for dep in deps:
            G.add_edge(package, dep)  # type: ignore[reportUnknownMember]

    return G


def has_cycles(G: nx.DiGraph) -> List[Any]:
    return list(nx.simple_cycles(G))  # type: ignore[reportUnknownMember]


def bfs_iterator(G: nx.DiGraph, start_node_name: str) -> List[str]:
    bfs_tree = nx.bfs_tree(G, start_node_name, reverse=True)
    return iter(bfs_tree.nodes())

from pprint import pprint
from booty.ast_util import get_dependencies, get_executable_index, get_recipe_definition_index
from booty.dependencies import get_dependency_graph
from booty.execute import SystemconfData, check_status_all

from booty.parser import parse
from booty.validation import validate

# # Read the grammer from ./grammar.lark
# with open("./booty/grammar.lark") as f:
#     grammer = f.read()
#
# # Create a Lark instance
# lark = Lark(grammer, debug=True)
#
#
# read file ./experiments/haskel_like.hk

with open("./experiments/haskel_like.hk") as f:
    example = f.read()

foo = """

recipe apt(packages):
  setup: sudo apt-get install -y $((packages))
  is_setup:
    for pkg in $(echo $((variables.packages)) | tr " " "\\n"); do
      if ! dpkg -l "$pkg" &> /dev/null; then
        echo "$pkg is not installed."
      else
        echo "$pkg is installed."
      fi
    done


recipe git(repo branch):
    setup: git clone -b $((branch)) $((repo))
    is_setup: test -d $((repo))
"""

foo2 = f"""
{foo}

pyenv -> pipx
pyenv <- python3.7 python3.8 python3.9 python3.10
pyenv:
    setup: 
        apt(build-essential libssl-dev zlib1g-dev libncurses5-dev 
            libncursesw5-dev libreadline-dev libsqlite3-dev libgdbm-dev 
            libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev tk-dev libffi-dev)
        curl https://pyenv.run | bash
        curl https://pyenv.run | bash
        foo(a b c)

    is_setup: which pyenv

foo: apt(a b c)
"""

simple = """
foo: apt(a b c)
"""

# ast = lark.parse(example)


# def get_target_names(ast: ParseTree) -> List[str]:
#     results = list(ast.find_pred(lambda x: x.data == "target_name"))
#     targets = [str(it.children[0]) for it in results]
#     return targets
#
#
# def get_dependencies(ast: ParseTree) -> Dict[str, List[str]]:
#     depends_on = list(ast.find_pred(lambda x: x.data == "depends_on"))
#     deppended_upon = list(ast.find_pred(lambda x: x.data == "depended_upon"))
#     dependencies: Dict[str, List[str]] = {}
#     for it in depends_on:
#         target_name = str(it.children[0])
#         dependencies[target_name] = dependencies.get(target_name, None) or []
#         for dep in it.children[1:]:
#             dependencies[target_name].append(str(dep))
#
#     for it in deppended_upon:
#         target_name = str(it.children[0])
#
#         dependencies[target_name] = dependencies.get(target_name, None) or []
#         for dep in it.children[1:]:
#             dependencies[str(dep)] = dependencies.get(str(dep), None) or []
#             dependencies[str(dep)].append(target_name)
#
#     return dependencies
#
#
# def get_dependency_graph(dependencies: Dict[str, List[str]]) -> nx.DiGraph:
#     G = nx.DiGraph()
#     for package, deps in dependencies.items():
#         for dep in deps:
#             G.add_edge(package, dep)  # type: ignore[reportUnknownMember]
#
#     return G


ast = parse(example)
# print(ast.pretty())
dependencies = get_dependencies(ast)
G = get_dependency_graph(dependencies)

# no_dependency_packages = get_zero_dependency_targets(dependencies)
# print()
# print("No dependency packages:")
# pprint(no_dependency_packages)

# cycles = list(nx.simple_cycles(G))  # type: ignore[reportUnknownMember]
# print()
# print("Cycles found:")
# pprint(cycles)


# print()
# print("Dependencies:")
# pprint(get_dependencies(ast))

# print()
# print("Full graph")
# pprint(list(G.nodes()))
# pprint(list(G.edges()))

# print()
# print("BFS")
# it = bfs_iterator(G, no_dependency_packages[0])
# print(list(it))


executables = get_executable_index(ast)
# print()
# print("Executables:")
# pprint(executables, width=180)

# recipe_definitions = get_recipe_definitions(ast)
# print()
# print("Recipe Definitions:")
print("======= Executables =======")
pprint(executables, width=180)

recipes = get_recipe_definition_index(ast)
print("======= Recipes =======")
pprint(recipes, width=180)


conf = SystemconfData(execution_index=executables, recipe_index=recipes, G=G, ast=ast)

validate(conf)

check_status_all(conf)

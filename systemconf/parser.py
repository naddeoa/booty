from typing import Optional
from lark import Lark, ParseTree

__parser: Optional[Lark] = None


def parse(text: str) -> ParseTree:
    global __parser
    if __parser is None:
        grammar_file = "./systemconf/grammar.lark"
        with open(grammar_file) as f:
            grammer = f.read()
        __parser = Lark(grammer, debug=True)

    return __parser.parse(text)

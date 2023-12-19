from typing import Optional
from lark import Lark, ParseTree
from pathlib import Path

__parser: Optional[Lark] = None


def get_lang_path(file: str) -> Path:
    current_file_path = Path(__file__).resolve()
    current_dir_path = current_file_path.parent
    return current_dir_path / "lang" / file


def parse(text: str) -> ParseTree:
    global __parser
    if __parser is None:
        with open(get_lang_path("grammar.lark")) as f:
            grammer = f.read()
        __parser = Lark(grammer, debug=True)

    return __parser.parse(text)

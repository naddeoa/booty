from typing import Optional
from lark import Lark, ParseTree
from pathlib import Path

from booty.lang import get_grammar

__parser: Optional[Lark] = None


def get_lang_path(file: str) -> Path:
    current_file_path = Path(__file__).resolve()
    current_dir_path = current_file_path.parent
    return current_dir_path / "lang" / file


def parse(text: str) -> ParseTree:
    global __parser
    if __parser is None:
        __parser = Lark(get_grammar(), debug=True)

    return __parser.parse(text)

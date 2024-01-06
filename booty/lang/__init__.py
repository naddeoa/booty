import sys
import os
from typing import cast


def __get_file_content(file_name: str) -> str:
    is_binary = getattr(sys, "_MEIPASS", None)
    here: str = cast(str, os.path.join(sys._MEIPASS, "booty", "lang") if is_binary else os.path.dirname(__file__))  # type: ignore
    with open(os.path.join(here, file_name), "r") as f:
        return f.read()


def get_stdlib() -> str:
    return __get_file_content("stdlib.booty")


def get_grammar() -> str:
    return __get_file_content("grammar.lark")

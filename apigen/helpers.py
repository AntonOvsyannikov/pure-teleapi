from textwrap import wrap
from typing import List


def quote_description(description: str) -> str:
    return description.replace('"', '\\"')


def format_description(description: str) -> List[str]:
    res = []
    paragraphs = quote_description(description).split("\n")
    for p in paragraphs:
        res.extend(wrap(p))
        res.append("")
    if res:
        res = res[:-1]
    return res


def formatted(description: str, prefix: str = "", first_line_prefix=None) -> str:
    if first_line_prefix is None:
        first_line_prefix = prefix
    fd = format_description(description)
    return "\n".join([first_line_prefix + fd[0]] + [prefix + l for l in fd[1:]])

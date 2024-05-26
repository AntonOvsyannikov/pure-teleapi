from copy import copy
from pathlib import Path
from typing import List

import httpx as httpx
from bs4 import BeautifulSoup

from apigen.models import ApiElement


def load_apidoc(apidoc_url: str) -> str:
    apidoc_path = Path(__file__).parent / ".apidoc.html"
    try:
        with open(apidoc_path, encoding="utf-8") as f:
            apidoc = f.read()
    except FileNotFoundError:
        apidoc = httpx.get(apidoc_url).text
        with open(apidoc_path, "w", encoding="utf-8") as f:
            f.write(apidoc)
    return apidoc


def split_soup(soup: BeautifulSoup, by_tag: str) -> List[BeautifulSoup]:
    res = []
    for e in soup.find_all(by_tag):
        ssoup = BeautifulSoup("", "html.parser")
        ssoup.append(copy(e))
        for s in e.find_next_siblings():
            if s.name == by_tag:  # noqa
                break
            ssoup.append(s)
        res.append(ssoup)
    return res


def get_table_header(table) -> List[str]:
    return [e.text.strip() for e in table.find("thead").find("tr").find_all("th")]


def get_table_content(table) -> List[List[str]]:
    return [[e.text.strip() for e in row.find_all("td")] for row in table.find("tbody").find_all("tr")]


def parse_apidoc(apidoc: str) -> List[ApiElement]:
    res = []
    h3s = split_soup(BeautifulSoup(apidoc, "html.parser"), "h3")

    for h3soup in h3s[4:]:
        section = h3soup.find_next("h3").text

        for h4soup in split_soup(h3soup, "h4"):
            h4 = h4soup.find_next("h4")
            title = h4.text
            ps = []
            for p in h4.find_next_siblings():
                if p.name != "p" or p.find("table"):  # noqa
                    break
                ps.append(p.text)
            description = "\n".join(ps)

            apiel = ApiElement(
                section=section,
                title=title,
                description=description,
            )

            if table := h4soup.find("table"):
                apiel.table_header = get_table_header(table)
                apiel.table = get_table_content(table)

            if ul := h4soup.find("ul"):
                apiel.ul = [li.text.strip() for li in ul.find_all("li")]

            res.append(apiel)

    return res

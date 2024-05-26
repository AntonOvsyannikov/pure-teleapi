from pathlib import Path
from shutil import rmtree

from apigen.models import Api


def gen(api: Api):
    gen_path = Path(__file__).parent / ".generated"

    rmtree(gen_path, ignore_errors=True)
    gen_path.mkdir(exist_ok=False)

    with open(gen_path / "teleapi.py", "w", encoding="utf-8") as f:
        api.gen(f)

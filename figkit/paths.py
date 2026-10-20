"""Where data and figures live. Override with NUMRUG_DATA / NUMRUG_OUT."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("NUMRUG_DATA", ROOT / "data")).expanduser()
OUT = Path(os.environ.get("NUMRUG_OUT", ROOT / "out")).expanduser()


def data(group: str, *parts: str) -> Path:
    """data/<group>/<parts...>; the group's prepare steps write here and its figures read here."""
    return DATA.joinpath(group, *parts)


def group_dir(group: str) -> Path:
    return ROOT / "groups" / group

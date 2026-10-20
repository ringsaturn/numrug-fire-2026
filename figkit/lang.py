"""Language switch shared by every figure script.

A figure script does, before it draws anything::

    from figkit import lang
    lang.init(__file__)            # parses --lang, loads the catalogs, sets fonts
    plt.title(lang.T("vis.title", time=lang.mdhm(t)))
    fig.savefig(lang.out("ahi-vis-20261011-1300"))

Strings live in TOML catalogs, never in the script:

- ``i18n/<lang>.toml``: shared formats (``[fmt]``) and the glossary.
- ``groups/<group>/i18n/<lang>.toml``: one table per figure.

A key missing from the selected language falls back to English with a warning,
so a partial translation still renders and the warning lists what is left.
"""

from __future__ import annotations

import glob
import os
import sys
import tomllib
from datetime import datetime
from pathlib import Path

from . import paths

LANG = "en"
GROUP: str | None = None
_cat: dict[str, str] = {}
_fallback: dict[str, str] = {}
_fmt: dict[str, str] = {}
_missing: set[str] = set()


def _flatten(d: dict, prefix: str = "") -> dict[str, str]:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, key + "."))
        else:
            out[key] = v
    return out


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _catalog(lang: str, group: str | None) -> tuple[dict[str, str], dict[str, str], dict]:
    shared = _load(paths.ROOT / "i18n" / f"{lang}.toml")
    fmt = shared.pop("fmt", {})
    fonts = shared.pop("fonts", {})
    cat = _flatten(shared)
    if group:
        g = _load(paths.ROOT / "groups" / group / "i18n" / f"{lang}.toml")
        gfonts = g.pop("fonts", {})
        fonts = {**fonts, **gfonts}
        cat.update(_flatten(g))
    return cat, fmt, fonts


def _parse_lang(argv: list[str]) -> str:
    """Take --lang X out of argv (so scripts that read sys.argv positionally keep working)."""
    lang = os.environ.get("FIG_LANG", "en")
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            lang = argv[i + 1]
            del argv[i : i + 2]
            break
        if a.startswith("--lang="):
            lang = a.split("=", 1)[1]
            del argv[i]
            break
    return lang


def init(
    script: str | None = None,
    group: str | None = None,
    lang: str | None = None,
    fonts: bool = True,
    figure: str | None = None,
) -> str:
    """Select the language and load catalogs; the group defaults to the one the script sits in.

    With ``figure``, a ``fonts`` table inside that figure's catalog table overrides
    the group and shared fonts (``[fire-weather-20261013.fonts]``).
    """
    global LANG, GROUP, _cat, _fallback, _fmt
    LANG = lang or _parse_lang(sys.argv)
    if group is None and script is not None:
        p = Path(script).resolve()
        if paths.ROOT / "groups" in p.parents:
            group = p.relative_to(paths.ROOT / "groups").parts[0]
    GROUP = group
    _cat, _fmt, font_cfg = _catalog(LANG, group)
    if LANG != "en":
        _fallback, fb_fmt, _ = _catalog("en", group)
        _fmt = {**fb_fmt, **_fmt}
    else:
        _fallback = {}
    if figure:
        own = {k[len(figure) + 7 :]: v for k, v in _cat.items() if k.startswith(f"{figure}.fonts.")}
        font_cfg = {**font_cfg, **own}
    if fonts:
        setup_fonts(font_cfg)
    import atexit

    atexit.register(_report_missing)
    return LANG


def setup_fonts(cfg: dict | None = None) -> None:
    """Register the font files listed for this language and set the family list.

    ``files`` entries are glob patterns; the ones not installed on this machine
    are skipped, so the same catalog works on macOS and Linux (Noto CJK).
    """
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    if cfg is None:
        _, _, cfg = _catalog(LANG, GROUP)
    for pattern in cfg.get("files", []) + os.environ.get("FIG_FONT_FILES", "").split(os.pathsep):
        for f in glob.glob(os.path.expanduser(pattern)) if pattern else []:
            font_manager.fontManager.addfont(f)
    if cfg.get("family"):
        # Drop families this machine lacks (Noto on macOS, Hiragino on Linux) so
        # matplotlib does not warn on every glyph lookup; generic names stay.
        have = {f.name for f in font_manager.fontManager.ttflist}
        generic = {"serif", "sans-serif", "monospace", "cursive", "fantasy"}
        fam = [f for f in cfg["family"] if f in have or f in generic]
        plt.rcParams["font.family"] = fam or ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def T(key: str, **kw) -> str:
    """The string for ``key`` in the selected language, formatted with ``kw``."""
    s = _cat.get(key)
    if s is None:
        s = _fallback.get(key)
        if s is None:
            raise KeyError(f"no string '{key}' in groups/{GROUP}/i18n/en.toml")
        _missing.add(key)
    return s.format(**kw) if kw else s


def has(key: str) -> bool:
    return key in _cat or key in _fallback


def _report_missing() -> None:
    if _missing:
        print(
            f"[figkit] {LANG}: {len(_missing)} string(s) fell back to English: " + ", ".join(sorted(_missing)),
            file=sys.stderr,
        )


# Formatting. Patterns come from [fmt] in i18n/<lang>.toml so that a translation
# changes date order, separators and digits without touching the scripts.


def _f(name: str, **kw) -> str:
    return _fmt[name].format(**kw)


def md(t: datetime) -> str:
    """Short date inside a panel: en 10-12, ja 10/12."""
    return _f("md", m=t.month, d=t.day)


def hm(t: datetime) -> str:
    return _f("hm", H=t.hour, M=t.minute)


def mdhm(t: datetime) -> str:
    return _f("mdhm", m=t.month, d=t.day, H=t.hour, M=t.minute)


def ymd(t: datetime) -> str:
    """Date in a title, where the year is allowed."""
    return _f("ymd", Y=t.year, m=t.month, d=t.day)


def num(x: float, nd: int = 0) -> str:
    """Number with the language's thousands separator."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "\0").replace(".", _fmt.get("decimal", ".")).replace("\0", _fmt.get("thousands", ","))


def out(name: str, ext: str = "png") -> str:
    """Output path for a figure: out/<name>.<lang>.<ext>."""
    paths.OUT.mkdir(parents=True, exist_ok=True)
    return str(paths.OUT / f"{name}.{LANG}.{ext}")

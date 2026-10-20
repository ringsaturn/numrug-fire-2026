"""numrug-figs: list, prepare and render the figures declared in groups/*/figures.toml.

    numrug-figs list
    numrug-figs prepare [--group G] [STEP ...]     # fetch and derive the inputs into data/<group>/
    numrug-figs render --lang ja [--group G] [NAME ...]
    numrug-figs webp --lang ja                     # out/*.ja.png -> out/webp/, as published
    numrug-figs compare A.png B.png                # size and mean |diff| of two renders

figures.toml (one per group)::

    [[prepare]]                   # run in order by `prepare`
    name = "ahi-download"
    run = ["scripts/dl_all.sh"]   # argv, relative to the group dir
    about = "Himawari-9 B07/B14 HSD segments from the NOAA open-data bucket (3.6 GB)"

    [[figure]]
    name = "ahi-vis-20261011-1300"            # published asset stem
    run = ["scripts/vis.py", "20261011_0500"]  # --lang is appended
    outputs = ["ahi-vis-20261011-1300"]        # optional, defaults to [name]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tomllib
from pathlib import Path

from . import paths


def _groups(only: str | None):
    for f in sorted((paths.ROOT / "groups").glob("*/figures.toml")):
        g = f.parent.name
        if only and g != only:
            continue
        with open(f, "rb") as fh:
            yield g, tomllib.load(fh)


def _exec(group: str, argv: list[str], extra: list[str]) -> int:
    gdir = paths.group_dir(group)
    cmd = list(argv)
    if cmd[0].endswith(".py"):
        cmd = [sys.executable, cmd[0], *cmd[1:]]
    elif cmd[0].endswith(".sh"):
        cmd = ["bash", *cmd]
    env = dict(
        os.environ,
        NUMRUG_DATA=str(paths.DATA),
        NUMRUG_OUT=str(paths.OUT),
        PYTHONPATH=os.pathsep.join(
            filter(None, [str(paths.ROOT), str(gdir / "scripts"), os.environ.get("PYTHONPATH")])
        ),
    )
    print("+", group, " ".join(cmd + extra), flush=True)
    return subprocess.call(cmd + extra, cwd=gdir, env=env)


def cmd_list(a):
    for g, spec in _groups(a.group):
        print(f"[{g}]")
        for s in spec.get("prepare", []):
            print(f"  prepare  {s['name']:<40} {s.get('about', '')}")
        for f in spec.get("figure", []):
            print(f"  figure   {f['name']}")


def cmd_prepare(a):
    rc = 0
    for g, spec in _groups(a.group):
        for s in spec.get("prepare", []):
            if a.names and s["name"] not in a.names:
                continue
            rc |= _exec(g, s["run"], [])
    return rc


def cmd_render(a):
    failed = []
    for g, spec in _groups(a.group):
        for f in spec.get("figure", []):
            if a.names and f["name"] not in a.names:
                continue
            if _exec(g, f["run"], ["--lang", a.lang]):
                failed.append(f["name"])
    if failed:
        print("failed:", ", ".join(failed), file=sys.stderr)
    return 1 if failed else 0


def cmd_webp(a):
    from PIL import Image

    dst = paths.OUT / "webp"
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(paths.OUT.glob(f"*.{a.lang}.png")):
        name = p.name[: -len(f".{a.lang}.png")]
        # The Chinese originals were published without a language suffix.
        q = dst / (f"{name}.webp" if a.lang == "zh" else f"{name}.{a.lang}.webp")
        Image.open(p).save(q, "WEBP", quality=82, method=6)
        print(q)


def cmd_compare(a):
    import numpy as np
    from PIL import Image

    x = np.asarray(Image.open(a.a).convert("RGB"), dtype=np.int16)
    y = np.asarray(Image.open(a.b).convert("RGB"), dtype=np.int16)
    print(f"size {x.shape[1]}x{x.shape[0]} vs {y.shape[1]}x{y.shape[0]}")
    if x.shape == y.shape:
        d = np.abs(x - y)
        print(f"mean |diff| {d.mean():.3f}  max {d.max()}  pixels differing {(d.max(axis=2) > 0).mean() * 100:.3f} %")


def main(argv=None):
    p = argparse.ArgumentParser(prog="numrug-figs")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list")
    s.add_argument("--group")
    s.set_defaults(fn=cmd_list)
    s = sub.add_parser("prepare")
    s.add_argument("--group")
    s.add_argument("names", nargs="*")
    s.set_defaults(fn=cmd_prepare)
    s = sub.add_parser("render")
    s.add_argument("--lang", default="en")
    s.add_argument("--group")
    s.add_argument("names", nargs="*")
    s.set_defaults(fn=cmd_render)
    s = sub.add_parser("webp")
    s.add_argument("--lang", default="en")
    s.set_defaults(fn=cmd_webp)
    s = sub.add_parser("compare")
    s.add_argument("a")
    s.add_argument("b")
    s.set_defaults(fn=cmd_compare)
    a = p.parse_args(argv)
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()

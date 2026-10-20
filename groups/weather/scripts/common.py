"""Shared helpers for the weather group: data paths and date tick labels."""

from __future__ import annotations

from figkit import lang, paths

GROUP = "weather"
USER_AGENT = "numrug-fire-2026/1.0"


def data(*parts: str):
    """data/weather/<parts...>"""
    return paths.data(GROUP, *parts)


def date_ticks(key: str, tz=None):
    """A tick formatter that renders each date tick through the catalog string ``key``.

    The string may use {md}, {hm}, {H}: e.g. "{md}\\n{hm}" draws 10-13 / 20:00.
    """
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter

    def fmt(x, pos=None):
        d = mdates.num2date(x, tz)
        return lang.T(key, md=lang.md(d), hm=lang.hm(d), H=d.hour)

    return FuncFormatter(fmt)

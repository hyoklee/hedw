"""hedw_report and hedw_day: run results and hourly data without the shell.

Both load code from the hedw repo (HEDW_ROOT, default ~/hedw): agent/report.py
for the digest and agent/coherence.py for the loaders, so tool and scripts share
one implementation. Read-only.
"""

import importlib.util
import os
from pathlib import Path

from clio_agent.sdk import tool


def _root() -> Path:
    return Path(os.environ.get("HEDW_ROOT", "~/hedw")).expanduser()


def _load(name):
    spec = importlib.util.spec_from_file_location(f"hedw_{name}", _root() / "agent" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _runs():
    res = (_root() / "agent" / "results").resolve()
    return res, sorted(p for p in res.glob("run_*") if (p / "summary.json").is_file())


@tool(read_only=True, defer=False, callers="direct")
def hedw_report(run: str = "", city: str = "") -> str:
    """Headline numbers of a HEDW-US solar-coherence run from its summary.json:
    cities, r_hourly / r_daily / bias distributions, best lags, physics checks,
    anomalous cities with their flags. With `city` (e.g. Texas_Dallas): that city's
    metrics and its top anomalous days. `run` is a run name or empty for the latest.
    Authoritative; needs no cross-check."""
    res, runs = _runs()
    if not runs:
        return f"no finished runs in {res}"
    target = runs[-1] if not run else (res / Path(run).name).resolve()
    if target not in runs:
        return f"no finished run {run!r}; finished runs: " + ", ".join(p.name for p in runs)
    return _load("report").digest(str(target), city or None)


@tool(read_only=True, defer=False, callers="direct")
def hedw_day(city: str, date: str) -> str:
    """Hourly NSRDB GHI, solar zenith and NASA POWER all-sky and clear-sky
    irradiance (W/m2, UTC) for one city and day (date = YYYY-MM-DD, 2019-2023),
    with the daily totals in Wh/m2, plus NSRDB's fill flag (percent of the hour
    gap-filled; 100 = no retrieval) and cloud type when available. Read from the
    raw files; authoritative."""
    co = _load("coherence")
    root = _root()
    name = city.strip()
    y = date[:4]
    f = root / "raw" / "nsrdb" / f"{name}_{y}.csv"
    if not f.is_file():
        return f"no NSRDB file {f.name}; city names look like Texas_Dallas"
    ns, _ = co.load_nsrdb(str(f))
    pw, _ = co.load_power(str(root / "raw" / "power" / f"{name}.json"))
    d = ns.loc[date].join(pw.loc[date], how="inner")
    fl = root / "raw" / "nsrdb" / "flags" / f"{name}_{y}_flags.csv"
    if fl.is_file():
        ff = _load("fillflags")
        d = d.join(ff.load(name).loc[date][["Fill Flag", "Cloud Type"]], how="left")
    lines = ["hour_utc ghi_nsrdb zen power_allsky power_clear"
             + (" nsrdb_fill_pct nsrdb_cloud_type" if "Fill Flag" in d else "")]
    for t, r in d.iterrows():
        extra = f" {r['Fill Flag']:.0f} {r['Cloud Type']:.0f}" if "Fill Flag" in d else ""
        lines.append(f"{t.hour:02d} {r.GHI:.0f} {r.zen:.1f} {r.ALLSKY_SFC_SW_DWN:.0f} "
                     f"{r.CLRSKY_SFC_SW_DWN:.0f}{extra}")
    lines.append(f"daily Wh/m2: nsrdb {d.GHI.sum():.0f} power {d.ALLSKY_SFC_SW_DWN.sum():.0f} "
                 f"power_clear {d.CLRSKY_SFC_SW_DWN.sum():.0f}")
    return "\n".join(lines)

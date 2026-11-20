#!/usr/bin/env python3
"""Ground truth for Honolulu inside the HEDW-US period: Hawaii Mesonet (HCDP)
stations 0501 Lyon Arboretum and 0502 Nuuanu Reservoir 1, 2022-04-16..2023-12-31,
vs NSRDB (the HEDW-US source) and NASA POWER.

HCDP SWin_1_Avg: 5-min mean, UTC timestamps. Campbell loggers stamp the END of
the interval (assumed; the lag scan against POWER checks the hour alignment).
Hourly mean over [H, H+1) needs >= 10 of 12 values.

Both stations sit 4-7 km inland of Honolulu city hall, at the mouths of the
Manoa and Nuuanu valleys, which are cloudier and wetter than the coastal
downtown. So (a) products at the station coordinates vs the station is the
fair test of each product; (b) Honolulu city-hall products vs the stations
mixes product error with real cloud gradient and is reported for context only.
usage: validate_hcdp.py <out_dir>
"""
import json, os, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "agent/ground"))
sys.path.insert(0, os.path.join(ROOT, "agent"))
import validate_local as vl  # noqa: E402

START, END = "2022-04-16", "2024-01-01"


def load(sid):
    d = pd.read_csv(os.path.join(ROOT, "raw/ground/hcdp", f"{sid}.csv"))
    t = pd.to_datetime(d.timestamp_utc, utc=True) - pd.Timedelta(minutes=5)   # interval start
    v = pd.to_numeric(d.swin_wm2, errors="coerce")
    s = pd.Series(v.where((v > -50) & (v < 1500)).clip(lower=0).values, index=t)
    s = s[~s.index.duplicated()]
    cnt = s.resample("1h").count()
    return s.resample("1h").mean().where(cnt >= 10)[START:END]


def clip(ns, pw):
    return ns[START:END], pw[START:END]


def lag(g, pw):
    j = pd.DataFrame({"g": g, "p": pw.ALLSKY_SFC_SW_DWN}).dropna()
    return {str(L): round(vl.corr(j.g.values, j.p.shift(L).values), 4) for L in (-1, 0, 1)}


def anom(mb):
    g = lambda k, ms: float(np.mean([mb[m][k] for m in ms if m in mb]))
    return {p: round(g(f"{p}_mbe_pct", (6, 7, 8)) - g(f"{p}_mbe_pct", (12, 1, 2)), 1) for p in ("nsrdb", "power")}


def main(out):
    os.makedirs(os.path.join(out, "figures"), exist_ok=True)
    res = {}
    for sid, name in [("0501", "HCDP_0501_Lyon"), ("0502", "HCDP_0502_Nuuanu")]:
        g = load(sid)
        for label, prod in [(f"{name}: products at the station", name),
                            (f"{name}: Honolulu city-hall products (HEDW-US request)", "Hawaii_Honolulu")]:
            ns, pw = clip(*vl.products(prod))
            r = vl.compare(g, ns, pw, label)
            r["lag_scan_r_vs_power"] = lag(g, pw)
            r["summer_minus_winter"] = anom(r["monthly_bias_vs_ground"])
            res[f"{sid}_vs_{prod}"] = r
    json.dump(res, open(os.path.join(out, "summary.json"), "w"), indent=1)
    for k, v in res.items():
        print(f"{k}: days {v['days']} lag {v['lag_scan_r_vs_power']}")
        print(f"   daily r N/P {v['daily']['nsrdb']['r']}/{v['daily']['power']['r']} | MBE% {v['daily']['nsrdb']['mbe_pct']}/{v['daily']['power']['mbe_pct']}"
              f" | RMSE% {v['daily']['nsrdb']['rmse_pct']}/{v['daily']['power']['rmse_pct']} | NSRDB closer {v['daily_nsrdb_closer_frac']}"
              f" | JJA-DJF {v['summer_minus_winter']}")
        print("   monthly:", {m: (x['nsrdb_mbe_pct'], x['power_mbe_pct']) for m, x in v['monthly_bias_vs_ground'].items()})

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    keys = [k for k in res if not k.endswith("Hawaii_Honolulu")]
    fig, axes = plt.subplots(1, len(keys), figsize=(11, 4), sharey=True)
    for ax, k in zip(axes, keys):
        mb = res[k]["monthly_bias_vs_ground"]; ms = sorted(mb)
        ax.plot(ms, [mb[m]["nsrdb_mbe_pct"] for m in ms], "o-", label="NSRDB (HEDW-US source)")
        ax.plot(ms, [mb[m]["power_mbe_pct"] for m in ms], "s-", label="NASA POWER")
        ax.axhline(0, color="k", lw=0.6); ax.set_xticks(range(1, 13)); ax.set_xlabel("month")
        ax.set_title(res[k]["label"], fontsize=9)
    axes[0].set_ylabel("monthly bias vs Mesonet (%)"); axes[0].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(out, "figures/monthly_bias_hcdp.png"), dpi=110); plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1])

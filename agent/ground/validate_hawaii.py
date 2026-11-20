#!/usr/bin/env python3
"""Ground truth for Honolulu: NLR MIDC stations in Hawaii vs NSRDB and NASA POWER.

- MIDC OAHURS1M (SOLRMAP Kalaeloa, Oahu; RSR), 2010-03-16..2011-11-01, ~23 km
  west of Honolulu city hall. Outside the HEDW-US period: tests whether either
  product misreads Honolulu's coastal leeward setting. Also compares the
  Honolulu city-hall series (the HEDW-US request) for 2010-2011.
- MIDC NELHA (Kona coast, Big Island), 2019-2023: in-period tropical-island
  coastal analogue (~260 km from Honolulu).
MIDC files: 1-min, field HST = HHMM (UTC-10), minute stamped at its end,
"Global Horizontal [W/m^2]". Reuses compare()/products() from validate_local.py.
usage: validate_hawaii.py <out_dir>
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "agent/ground"))
sys.path.insert(0, os.path.join(ROOT, "agent"))
import validate_local as vl  # noqa: E402


def load_midc(pattern, clock="HST", utc_offset_h=10):
    parts = []
    for f in sorted(glob.glob(os.path.join(ROOT, "raw/ground/midc", pattern))):
        parts.append(pd.read_csv(f, usecols=["Year", "DOY", clock, "Global Horizontal [W/m^2]"]))
    d = pd.concat(parts)
    hh, mm = d[clock] // 100, d[clock] % 100
    t = pd.to_datetime(d.Year.astype(str), format="%Y") + pd.to_timedelta(d.DOY - 1, unit="D") \
        + pd.to_timedelta(hh, unit="h") + pd.to_timedelta(mm, unit="min")
    g = d["Global Horizontal [W/m^2]"].where(lambda x: (x > -50) & (x < 1500)).clip(lower=0)
    s = pd.Series(g.values, index=pd.DatetimeIndex(t + pd.Timedelta(hours=utc_offset_h)).tz_localize("UTC"))
    s.index = s.index - pd.Timedelta(minutes=1)          # minute stamped at its end
    s = s[~s.index.duplicated()]
    cnt = s.resample("1h").count()
    return s.resample("1h").mean().where(cnt >= 45)


def lag(g, pw):
    j = pd.DataFrame({"g": g, "p": pw.ALLSKY_SFC_SW_DWN}).dropna()
    return {str(L): round(vl.corr(j.g.values, j.p.shift(L).values), 4) for L in (-1, 0, 1)}


def anom(mb):
    g = lambda k, ms: float(np.mean([mb[m][k] for m in ms if m in mb]))
    return {p: round(g(f"{p}_mbe_pct", (6, 7, 8)) - g(f"{p}_mbe_pct", (12, 1, 2)), 1) for p in ("nsrdb", "power")}


def main(out):
    os.makedirs(os.path.join(out, "figures"), exist_ok=True)
    res = {}
    kal = load_midc("OAHURS1M_*.csv")
    for name, prod in [("Kalaeloa ground vs products at Kalaeloa (2010-2011)", "MIDC_Kalaeloa_Oahu"),
                       ("Kalaeloa ground vs Honolulu city-hall products (HEDW-US request, 23 km, 2010-2011)", "Hawaii_Honolulu")]:
        ns, pw = vl.products(prod, "_2010-2011")
        r = vl.compare(kal, ns, pw, name)
        r["lag_scan_r_vs_power"] = lag(kal, pw)
        r["summer_minus_winter"] = anom(r["monthly_bias_vs_ground"])
        res[prod + "_2010-2011"] = r
    nel = load_midc("NELHA_*.csv")
    ns, pw = vl.products("MIDC_NELHA_Kona")
    r = vl.compare(nel, ns, pw, "NELHA Kona ground vs products at NELHA (2019-2023)")
    r["lag_scan_r_vs_power"] = lag(nel, pw)
    r["summer_minus_winter"] = anom(r["monthly_bias_vs_ground"])
    res["MIDC_NELHA_Kona_2019-2023"] = r
    json.dump(res, open(os.path.join(out, "summary.json"), "w"), indent=1)

    for k, v in res.items():
        print(f"{k}: days {v['days']} lag {v['lag_scan_r_vs_power']}")
        print(f"   daily r NSRDB {v['daily']['nsrdb']['r']} POWER {v['daily']['power']['r']} | MBE% {v['daily']['nsrdb']['mbe_pct']} / {v['daily']['power']['mbe_pct']}"
              f" | RMSE% {v['daily']['nsrdb']['rmse_pct']} / {v['daily']['power']['rmse_pct']} | NSRDB closer {v['daily_nsrdb_closer_frac']}"
              f" | JJA-DJF {v['summer_minus_winter']} | episode days {v['episode_days']}")
        print("   monthly:", {m: (x['nsrdb_mbe_pct'], x['power_mbe_pct']) for m, x in v['monthly_bias_vs_ground'].items()})

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    for ax, (k, v) in zip(axes, res.items()):
        mb = v["monthly_bias_vs_ground"]; ms = sorted(mb)
        ax.plot(ms, [mb[m]["nsrdb_mbe_pct"] for m in ms], "o-", label="NSRDB (HEDW-US source)")
        ax.plot(ms, [mb[m]["power_mbe_pct"] for m in ms], "s-", label="NASA POWER")
        ax.axhline(0, color="k", lw=0.6); ax.set_xticks(range(1, 13)); ax.set_xlabel("month")
        ax.set_title(v["label"], fontsize=8)
    axes[0].set_ylabel("monthly bias vs ground (%)"); axes[0].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(out, "figures/monthly_bias_hawaii.png"), dpi=110); plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1])

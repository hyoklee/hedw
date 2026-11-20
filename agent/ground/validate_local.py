#!/usr/bin/env python3
"""Ground truth near the flagged cities: FAWN (Florida) and MIDC LMU (Los Angeles).

FAWN hourly summaries (raw/ground/fawn/<name>_<year>.csv): Date + Time are
local labels with no stated time zone; "Solar Radiation (w/m2)" is the hourly
mean. MIDC LMU (raw/ground/midc/LMU_<year>.csv): 1-min, PST (UTC-8), field
"PST" = HHMM; "Global Horizontal [W/m^2]".

1. Time convention: lag scan of the ground series against POWER (UTC hour
   means) for every candidate (fixed standard time vs local clock with DST;
   label = start vs end of the averaging hour), winter and summer separately.
2. NSRDB (value at H:30 UTC) and POWER (hour H mean) at the station
   coordinates vs ground: hourly/daily r, MBE, RMSE, monthly bias.
3. For the flagged cities: their own NSRDB/POWER series (city coordinates,
   the HEDW-US request) against the nearest station.

usage: validate_local.py <out_dir>
"""
import csv, glob, json, math, os, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "agent"))
import coherence as co  # noqa: E402

EPISODES = ["2019-11-17", "2019-11-18", "2019-11-19", "2019-11-20", "2020-02-13", "2020-02-14"]
FLAGGED_NEAR = {  # flagged city -> station used as ground truth (distance km from flagged_city_distances_*.txt)
    "Florida_FortLauderdale": ("FAWN_FortLauderdale", 11), "Florida_PembrokePines": ("FAWN_FortLauderdale", 10),
    "Florida_Hialeah": ("FAWN_FortLauderdale", 26), "Florida_Miami": ("FAWN_FortLauderdale", 36),
}


def load_fawn_local(name, era=None):
    """Naive local-label series. FAWN changed its export in 2021:
    2019-2020 'Date','Time','Solar Radiation (w/m2)'; 2021+ 'Date Time',
    'Solar Radiation (w/m2) Avg'. era: None (all), 'old' (<=2020) or 'new' (>=2021)."""
    parts = []
    for f in sorted(glob.glob(os.path.join(ROOT, "raw/ground/fawn", f"{name}_*.csv"))):
        yr = int(f[-8:-4])
        if era == "old" and yr > 2020 or era == "new" and yr < 2021:
            continue
        head = open(f).readline()
        if "Date Time" in head:
            d = pd.read_csv(f, usecols=["Date Time", "Solar Radiation (w/m2) Avg"])
            d["t"] = pd.to_datetime(d["Date Time"], errors="coerce")
            d["sr"] = d["Solar Radiation (w/m2) Avg"]
        else:
            d = pd.read_csv(f, usecols=["Date", "Time", "Solar Radiation (w/m2)"])
            d["t"] = pd.to_datetime(d.Date + " " + d.Time, errors="coerce")
            d["sr"] = d["Solar Radiation (w/m2)"]
        parts.append(d.dropna(subset=["t"])[["t", "sr"]])
    if not parts:
        raise FileNotFoundError(f"no FAWN files for {name} era={era}")
    d = pd.concat(parts)
    s = pd.to_numeric(d.sr, errors="coerce")
    s = s.where((s >= 0) & (s < 1500))
    return pd.Series(s.values, index=d.t.values).groupby(level=0).mean()  # naive local labels


def fawn_to_utc(local, conv):
    """conv = (clock, label): clock 'EST' fixed UTC-5 or 'local' America/New_York;
    label 'start' (label = start of the averaged hour) or 'end'."""
    clock, label = conv
    idx = local.index
    if clock == "EST":
        utc = idx + pd.Timedelta(hours=5)
    else:
        utc = pd.DatetimeIndex(idx).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT") \
            .tz_convert("UTC").tz_localize(None)
    if label == "end":
        utc = utc - pd.Timedelta(hours=1)
    s = pd.Series(local.values, index=pd.DatetimeIndex(utc).tz_localize("UTC"))
    return s[s.index.notna()].groupby(level=0).mean()


def load_lmu():
    parts = []
    for f in sorted(glob.glob(os.path.join(ROOT, "raw/ground/midc", "LMU_*.csv"))):
        d = pd.read_csv(f, usecols=["Year", "DOY", "PST", "Global Horizontal [W/m^2]"])
        parts.append(d)
    d = pd.concat(parts)
    hh, mm = d.PST // 100, d.PST % 100
    t = pd.to_datetime(d.Year.astype(str), format="%Y") + pd.to_timedelta(d.DOY - 1, unit="D") \
        + pd.to_timedelta(hh, unit="h") + pd.to_timedelta(mm, unit="min")
    g = d["Global Horizontal [W/m^2]"].where(lambda x: (x > -50) & (x < 1500)).clip(lower=0)
    s = pd.Series(g.values, index=pd.DatetimeIndex(t + pd.Timedelta(hours=8)).tz_localize("UTC"))
    # MIDC stamps a minute at its end: minute ending HH:MM covers (HH:MM-1, HH:MM]; shift 1 min back
    s.index = s.index - pd.Timedelta(minutes=1)
    cnt = s.resample("1h").count()
    return s.resample("1h").mean().where(cnt >= 45)


def _has(name, era):
    try:
        load_fawn_local(name, era)
        return True
    except FileNotFoundError:
        return False


def products(name, years_tag=""):
    yrs = range(2019, 2024) if not years_tag else range(int(years_tag[1:5]), int(years_tag[6:10]) + 1)
    ns = pd.concat([co.load_nsrdb(os.path.join(ROOT, "raw/nsrdb", f"{name}_{y}.csv"))[0] for y in yrs])
    pw, _ = co.load_power(os.path.join(ROOT, "raw/power", f"{name}{years_tag}.json"))
    return ns, pw


def corr(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() > 50 else float("nan")


def stats(obs, est):
    m = np.isfinite(obs) & np.isfinite(est)
    o, e = obs[m], est[m]
    if len(o) < 50:
        return {"n": int(len(o))}
    return {"n": int(len(o)), "r": round(float(np.corrcoef(o, e)[0, 1]), 4),
            "mbe_pct": round(float(100 * (e.sum() - o.sum()) / o.sum()), 2),
            "rmse_wm2": round(float(np.sqrt(np.mean((e - o) ** 2))), 1),
            "rmse_pct": round(float(100 * np.sqrt(np.mean((e - o) ** 2)) / o.mean()), 1)}


def compare(ground, ns, pw, label):
    j = pd.DataFrame({"ground": ground, "nsrdb": ns.GHI, "zen": ns.zen, "power": pw.ALLSKY_SFC_SW_DWN})
    h = j[(j.zen < 85) & j.ground.notna() & j.nsrdb.notna() & j.power.notna()]
    dd = h[["ground", "nsrdb", "power"]].resample("1D").agg(["sum", "count"])
    d = pd.DataFrame({k: dd[(k, "sum")] for k in ["ground", "nsrdb", "power"]})[dd[("ground", "count")] >= 6]
    # drop days where the ground total is implausibly low vs both products (sensor outage, partial zeros)
    bad = (d.ground < 0.3 * d[["nsrdb", "power"]].min(axis=1)) & (d[["nsrdb", "power"]].min(axis=1) > 1500)
    d = d[~bad]
    mon = {}
    for m in range(1, 13):
        x = d[d.index.month == m]
        if len(x) > 10:
            mon[m] = {"nsrdb_mbe_pct": round(float(100 * (x.nsrdb.sum() / x.ground.sum() - 1)), 1),
                      "power_mbe_pct": round(float(100 * (x.power.sum() / x.ground.sum() - 1)), 1)}
    ep = d[d.index.strftime("%Y-%m-%d").isin(EPISODES)]
    return {"label": label, "daylight_hours": int(len(h)), "days": int(len(d)), "days_dropped_ground_outage": int(bad.sum()),
            "hourly": {"nsrdb": stats(h.ground.values, h.nsrdb.values), "power": stats(h.ground.values, h.power.values)},
            "daily": {"nsrdb": stats(d.ground.values, d.nsrdb.values), "power": stats(d.ground.values, d.power.values)},
            "daily_nsrdb_closer_frac": round(float((np.abs(d.nsrdb - d.ground) < np.abs(d.power - d.ground)).mean()), 3),
            "monthly_bias_vs_ground": mon,
            "episode_days": [{"date": str(i.date()), "ground": round(float(r.ground)), "nsrdb": round(float(r.nsrdb)),
                              "power": round(float(r.power))} for i, r in ep.iterrows()]}


def time_convention(local, pw):
    res = {}
    for conv in [("EST", "start"), ("EST", "end"), ("local", "start"), ("local", "end")]:
        g = fawn_to_utc(local, conv)
        j = pd.DataFrame({"g": g, "p": pw.ALLSKY_SFC_SW_DWN}).dropna()
        out = {}
        for season, months in [("winter", [12, 1, 2]), ("summer", [6, 7, 8])]:
            x = j[j.index.month.isin(months)]
            out[season] = {str(L): round(corr(x.g.values, x.p.shift(L).values), 4) for L in (-1, 0, 1)}
        res[f"{conv[0]}/{conv[1]}"] = out
    best = max(res, key=lambda k: res[k]["winter"]["0"] + res[k]["summer"]["0"])
    return best, res


def main(out):
    os.makedirs(os.path.join(out, "figures"), exist_ok=True)
    summary = {"fawn": {}, "lmu": None, "flagged_cities": {}}
    sts = list(csv.DictReader(open(os.path.join(ROOT, "agent/ground/fawn_selected.csv"))))
    votes = {"old": {}, "new": {}}
    for st in sts:
        name = st["name"]
        summary["fawn"][name] = {"lat": float(st["lat"]), "lon": float(st["lon"]), "time_scan_r": {}}
        try:
            ns, pw = products(name)
        except (FileNotFoundError, ValueError) as e:
            summary["fawn"][name] = {"error": str(e)}
            continue
        for era in ("old", "new"):
            try:
                local = load_fawn_local(name, era)
            except FileNotFoundError:
                continue
            best, scan = time_convention(local, pw)
            votes[era][best] = votes[era].get(best, 0) + 1
            summary["fawn"][name]["time_scan_r"][era] = {"best": best, "scan": scan}
    conv = {era: max(v, key=v.get) for era, v in votes.items() if v}
    summary["fawn_time_convention"] = {"chosen": conv, "votes": votes}

    def fawn_ground(name):
        return pd.concat([fawn_to_utc(load_fawn_local(name, era), tuple(c.split("/")))
                          for era, c in conv.items()
                          if glob.glob(os.path.join(ROOT, "raw/ground/fawn", f"{name}_*.csv"))
                          and _has(name, era)]).sort_index()

    for st in sts:
        name = st["name"]
        if "error" in summary["fawn"][name]:
            continue
        ground = fawn_ground(name)
        ns, pw = products(name)
        summary["fawn"][name].update(compare(ground, ns, pw, name))
        if name == "FAWN_FortLauderdale":
            fl_ground = ground
    # flagged cities vs the Fort Lauderdale station (city-coordinate products, as in HEDW-US)
    for city, (stn, km) in FLAGGED_NEAR.items():
        ns, pw = products(city)
        r = compare(fl_ground, ns, pw, f"{city} products vs {stn} ground ({km} km)")
        r["station"], r["distance_km"] = stn, km
        summary["flagged_cities"][city] = r
    # LMU (Los Angeles coast, 2011-2014)
    g = load_lmu()
    ns, pw = products("MIDC_LMU_LosAngeles", "_2011-2014")
    lag = {}
    j = pd.DataFrame({"g": g, "p": pw.ALLSKY_SFC_SW_DWN}).dropna()
    for L in (-1, 0, 1):
        lag[str(L)] = round(corr(j.g.values, j.p.shift(L).values), 4)
    summary["lmu"] = compare(g, ns, pw, "MIDC LMU (Loyola Marymount, Los Angeles) 2011-2014")
    summary["lmu"]["lag_scan_r_vs_power"] = lag
    summary["lmu"]["note"] = "outside the HEDW-US period; tests the coastal-LA representativeness hypothesis"
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)

    with open(os.path.join(out, "stations.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station", "lat", "lon", "days", "nsrdb_daily_r", "power_daily_r", "nsrdb_daily_mbe_pct",
                    "power_daily_mbe_pct", "nsrdb_daily_rmse_pct", "power_daily_rmse_pct", "nsrdb_hourly_rmse_wm2",
                    "power_hourly_rmse_wm2", "daily_nsrdb_closer_frac"])
        rows = [(k, v) for k, v in summary["fawn"].items() if "daily" in v] + [("MIDC_LMU_2011-2014", summary["lmu"])] \
            + [(f"{k} (city products vs FAWN_FortLauderdale)", v) for k, v in summary["flagged_cities"].items()]
        for k, v in rows:
            w.writerow([k, v.get("lat", ""), v.get("lon", ""), v["days"], v["daily"]["nsrdb"]["r"], v["daily"]["power"]["r"],
                        v["daily"]["nsrdb"]["mbe_pct"], v["daily"]["power"]["mbe_pct"], v["daily"]["nsrdb"]["rmse_pct"],
                        v["daily"]["power"]["rmse_pct"], v["hourly"]["nsrdb"]["rmse_wm2"], v["hourly"]["power"]["rmse_wm2"],
                        v["daily_nsrdb_closer_frac"]])
    figures(out, summary)
    print(json.dumps({"fawn_time_convention": summary["fawn_time_convention"]}, indent=1))
    for k, v in rows:
        print(f"{k:60s} days {v['days']:5d}  daily RMSE% NSRDB {v['daily']['nsrdb']['rmse_pct']:5} POWER {v['daily']['power']['rmse_pct']:5}"
              f"  MBE% NSRDB {v['daily']['nsrdb']['mbe_pct']:6} POWER {v['daily']['power']['mbe_pct']:6}  NSRDB closer {v['daily_nsrdb_closer_frac']}")
    print("LMU lag scan r vs POWER:", summary["lmu"]["lag_scan_r_vs_power"])
    print("LMU monthly bias vs ground:", summary["lmu"]["monthly_bias_vs_ground"])
    print("Fort Lauderdale monthly bias vs ground:", summary["fawn"]["FAWN_FortLauderdale"]["monthly_bias_vs_ground"])


def figures(out, s):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, (title, rec) in zip(axes, [("FAWN Fort Lauderdale 2019-2023 (10-36 km from 4 flagged cities)", s["fawn"]["FAWN_FortLauderdale"]),
                                       ("MIDC LMU Los Angeles coast 2011-2014", s["lmu"])]):
        mb = rec["monthly_bias_vs_ground"]
        ms = sorted(int(m) for m in mb)
        ax.plot(ms, [mb[m]["nsrdb_mbe_pct"] for m in ms], "o-", label="NSRDB (HEDW-US source)")
        ax.plot(ms, [mb[m]["power_mbe_pct"] for m in ms], "s-", label="NASA POWER")
        ax.axhline(0, color="k", lw=0.6); ax.set_xticks(range(1, 13)); ax.set_xlabel("month")
        ax.set_title(title, fontsize=9)
    axes[0].set_ylabel("monthly bias vs ground (%)"); axes[0].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(out, "figures/monthly_bias_vs_ground.png"), dpi=110); plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1])

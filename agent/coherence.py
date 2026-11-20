#!/usr/bin/env python3
"""Per-city solar-coherence detector: NSRDB GHI (the HEDW-US solar source) vs
NASA POWER hourly ALLSKY_SFC_SW_DWN, 2019-01-01..2023-12-31 UTC.

Time convention (see wiki/concept-solar-coherence.md):
  * NSRDB GOES v4 hourly, utc=true: record Hour=H, Minute=30 is the value at
    H:30 UTC (W/m2).
  * POWER hourly, time-standard=UTC: key YYYYMMDDHH is the mean over
    [HH:00, HH+1:00) UTC (Wh/m2 for that hour == mean W/m2).
  So NSRDB H:30 is centred on POWER hour H: the expected best lag is 0 h.
  (In HEDW-US the same NSRDB H:30 value sits on row H:00, so the lag is 0 h
  there too, with labels 30 min early.)

For one city it emits one JSON line with per-year and all-years metrics plus a
list of anomalous days. Inputs: raw/nsrdb/<name>_<year>.csv, raw/power/<name>.json.
numpy + pandas only.
"""
import argparse, json, os, sys, time
import numpy as np
import pandas as pd

YEARS = range(2019, 2024)
NIGHT_ZEN = 96.0          # zenith beyond civil twilight: GHI must be ~0
NIGHT_GHI = 5.0           # W/m2 tolerated at night
DAY_MIN_POWER = 500.0     # Wh/m2/day: skip ratio tests on very dark days
LAGS = range(-3, 4)


def load_nsrdb(path):
    meta = pd.read_csv(path, nrows=1)
    df = pd.read_csv(path, skiprows=2)
    ts = pd.to_datetime(dict(year=df.Year, month=df.Month, day=df.Day, hour=df.Hour), utc=True)
    df.index = ts
    m = {"nsrdb_lat": float(meta["Latitude"][0]), "nsrdb_lon": float(meta["Longitude"][0]),
         "nsrdb_location_id": int(meta["Location ID"][0]), "nsrdb_elev_m": float(meta["Elevation"][0]),
         "minute_values": sorted(int(v) for v in df.Minute.unique())}
    return df[["GHI", "DNI", "DHI", "Solar Zenith Angle"]].rename(columns={"Solar Zenith Angle": "zen"}), m


def load_power(path):
    d = json.load(open(path))
    p = d["properties"]["parameter"]
    idx = pd.to_datetime(list(p["ALLSKY_SFC_SW_DWN"].keys()), format="%Y%m%d%H", utc=True)
    df = pd.DataFrame({k: list(v.values()) for k, v in p.items()}, index=idx, dtype=float)
    fill = d.get("header", {}).get("fill_value", -999.0)
    df = df.mask(df <= fill + 1e-6)
    g = d["geometry"]["coordinates"]
    return df, {"power_lon": g[0], "power_lat": g[1], "power_elev_m": g[2],
                "power_sources": d.get("header", {}).get("sources")}


def corr(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 10:
        return float("nan")
    return float(np.corrcoef(a[m], b[m])[0, 1])


def flat_runs(x, day, min_len=3):
    """Number of daytime hours inside runs of >= min_len identical non-zero values."""
    v = np.where(day & (x > 0), x, np.nan)
    same = np.r_[False, v[1:] == v[:-1]]
    n, run = 0, 1
    for s in same:
        if s:
            run += 1
        else:
            if run >= min_len:
                n += run
            run = 1
    if run >= min_len:
        n += run
    return int(n)


def metrics(j):
    """j: hourly frame with ghi (NSRDB), sw (POWER all-sky), clr (POWER clear-sky), zen."""
    g, s = j.ghi.to_numpy(float), j.sw.to_numpy(float)
    day = j.zen.to_numpy() < 90
    night = j.zen.to_numpy() > NIGHT_ZEN
    out = {"hours": int(len(j)), "nsrdb_missing": int(np.isnan(g).sum()), "power_missing": int(np.isnan(s).sum())}
    out["r_hourly"] = corr(g, s)
    out["r_hourly_day"] = corr(g[day], s[day])
    lagr = {L: corr(g, np.roll(s, L)) for L in LAGS}  # roll(+1): POWER shifted 1 h later
    out["best_lag_h"] = int(max(lagr, key=lambda L: -1 if np.isnan(lagr[L]) else lagr[L]))
    out["r_by_lag"] = {str(L): round(v, 4) for L, v in lagr.items()}
    d = j[["ghi", "sw", "clr"]].resample("1D").sum(min_count=20)
    out["r_daily"] = corr(d.ghi.to_numpy(), d.sw.to_numpy())
    out["mean_ghi_wm2"] = float(np.nanmean(g))
    out["mean_power_wm2"] = float(np.nanmean(s))
    out["bias_pct"] = float(100 * (np.nansum(g[np.isfinite(s)]) / np.nansum(s[np.isfinite(g)]) - 1))
    diff = g - s
    out["rmse_hourly_wm2"] = float(np.sqrt(np.nanmean(diff[day] ** 2)))
    out["mae_hourly_wm2"] = float(np.nanmean(np.abs(diff[day])))
    out["night_nonzero_frac"] = float(np.mean(g[night] > NIGHT_GHI)) if night.any() else 0.0
    out["night_max_wm2"] = float(np.nanmax(g[night])) if night.any() else 0.0
    out["negative_hours"] = int(np.sum(g < 0))
    out["flat_hours"] = flat_runs(g, day)
    dd = d[d.sw > DAY_MIN_POWER]
    out["over_clearsky_days_frac"] = float(np.mean(dd.ghi > 1.1 * dd.clr)) if len(dd) else 0.0
    out["physics_viol_frac"] = float((np.sum(g[night] > NIGHT_GHI) + np.sum(g < 0) + out["flat_hours"]) / len(g))
    return out


def anomalous_days(j, zthr=4.0, min_abs=1000.0, top=25):
    """Days whose NSRDB/POWER daily-total log ratio is a robust outlier (|z| > zthr)
    for this city AND whose totals differ by more than min_abs Wh/m2."""
    d = j[["ghi", "sw", "clr"]].resample("1D").sum(min_count=20).dropna()
    d = d[(d.sw > DAY_MIN_POWER) | (d.ghi > DAY_MIN_POWER)]
    lr = np.log((d.ghi + 50) / (d.sw + 50))      # log ratio, damped for dark days
    med = np.median(lr)
    mad = 1.4826 * np.median(np.abs(lr - med)) or 1e-9
    z = (lr - med) / mad
    hit = (np.abs(z) > zthr) & ((d.ghi - d.sw).abs() > min_abs)
    sel = d[hit].assign(z=z[hit]).sort_values("z", key=np.abs, ascending=False)
    rows = [{"date": str(i.date()), "nsrdb_whm2": round(float(r.ghi)), "power_whm2": round(float(r.sw)),
             "power_clear_whm2": round(float(r.clr)), "z": round(float(r.z), 2)} for i, r in sel.head(top).iterrows()]
    return int(len(sel)), rows, {"logratio_median": float(med), "logratio_mad": float(mad),
                                 "anomalous_days_low": int((sel.z < 0).sum()), "anomalous_days_high": int((sel.z > 0).sum())}


def analyse(name, root):
    t0 = time.time()
    parts, meta = [], {}
    for y in YEARS:
        f = os.path.join(root, "raw/nsrdb", f"{name}_{y}.csv")
        if not os.path.exists(f):
            return {"city": name, "error": f"missing {os.path.basename(f)}"}
        df, meta = load_nsrdb(f)
        parts.append(df)
    ns = pd.concat(parts)
    pw, pmeta = load_power(os.path.join(root, "raw/power", f"{name}.json"))
    j = pd.DataFrame({"ghi": ns.GHI, "zen": ns.zen}).join(
        pw.rename(columns={"ALLSKY_SFC_SW_DWN": "sw", "CLRSKY_SFC_SW_DWN": "clr"})[["sw", "clr"]], how="outer")
    rec = {"city": name, **meta, **pmeta, "nsrdb_rows": int(len(ns)), "power_rows": int(len(pw)),
           "joined_rows": int(len(j))}
    rec["years"] = {str(y): metrics(j[j.index.year == y]) for y in YEARS}
    rec["all"] = metrics(j)
    rec["monthly_bias_pct"] = {
        k.strftime("%Y-%m"): round(float(100 * (v.ghi / v.sw - 1)), 2)
        for k, v in j[["ghi", "sw"]].dropna().resample("1MS").sum().iterrows() if v.sw > 0}
    n, rows, st = anomalous_days(j)
    rec["anomalous_days"] = n
    rec["anomalous_day_list"] = rows
    rec.update(st)
    rec["elapsed_ms"] = round((time.time() - t0) * 1e3, 1)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cities", nargs="+", help="city names as in target_cities.csv")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--out", help="append JSON lines here (default stdout)")
    a = ap.parse_args()
    out = open(a.out, "a") if a.out else sys.stdout
    for c in a.cities:
        try:
            r = analyse(c, a.root)
        except Exception as e:
            r = {"city": c, "error": repr(e)}
        out.write(json.dumps(r, allow_nan=True) + "\n")
        out.flush()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Download NSRDB (HEDW-US solar source) and NASA POWER hourly data for every
target city, 2019-2023, into ../raw/nsrdb/ and ../raw/power/.

NSRDB request = the authors' 02_build_dataset.py parameters on the renamed host
(developer.nlr.gov). POWER = one hourly request per city for the full 5 years.
Resumable: existing non-empty files are skipped. Stdlib only.

usage: fetch_all.py [--cities raw/upstream/hedw-code/target_cities.csv]
                    [--only nsrdb|power] [--workers 3] [--limit N]
"""
import argparse, csv, json, os, sys, time, random, threading
import urllib.parse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
YEARS = range(2019, 2024)
NSRDB_URL = "https://developer.nlr.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv"
POWER_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
ATTRS = ("ghi,dni,dhi,air_temperature,wind_speed,wind_direction,dew_point,"
         "relative_humidity,surface_pressure,surface_albedo,solar_zenith_angle")
LOG_LOCK = threading.Lock()


def load_env(path=os.path.expanduser("~/.config/hedw/nlr.env")):
    env = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v.strip().strip('"')
    return env


def log(msg):
    with LOG_LOCK:
        print(time.strftime("%H:%M:%S"), msg, flush=True)


def get(url, params, out, check, tries=6):
    q = url + "?" + urllib.parse.urlencode(params)
    delay = 5.0
    for i in range(tries):
        try:
            req = urllib.request.Request(q, headers={"User-Agent": "hedw-fetch/1.0"})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read()
            check(body)
            tmp = out + ".part"
            with open(tmp, "wb") as f:
                f.write(body)
            os.replace(tmp, out)
            return len(body)
        except urllib.error.HTTPError as e:
            msg = e.read()[:300].decode("utf-8", "replace")
            log(f"  HTTP {e.code} {os.path.basename(out)} try {i+1}: {msg}")
            if e.code not in (429, 500, 502, 503, 504):
                return -e.code
        except Exception as e:  # network or validation
            log(f"  error {os.path.basename(out)} try {i+1}: {e}")
        time.sleep(delay + random.uniform(0, 2))
        delay *= 2
    return -1


def check_nsrdb(body):
    head = body[:4096].decode("utf-8", "replace").splitlines()
    if len(head) < 3 or not head[2].lower().startswith("year"):
        raise ValueError("not an NSRDB CSV: " + body[:200].decode("utf-8", "replace"))
    if body.count(b"\n") < 8760 + 2:
        raise ValueError("short file: %d lines" % body.count(b"\n"))


def check_power(body):
    d = json.loads(body)
    n = len(d["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"])
    if n < 8760 * len(YEARS):
        raise ValueError(f"POWER returned {n} hours")


FLAG_ATTRS = "ghi,clearsky_ghi,cloud_type,fill_flag"


def fetch_nsrdb(city, env, outdir, attrs=ATTRS, suffix=""):
    res = []
    for y in YEARS:
        out = os.path.join(outdir, f"{city['name']}_{y}{suffix}.csv")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            res.append((y, "skip")); continue
        p = {"api_key": env["NLR_API_KEY"], "names": str(y), "interval": "60",
             "utc": "true", "leap_day": "true", "email": env["NLR_EMAIL"],
             "affiliation": env["NLR_AFFILIATION"], "reason": "Academic Research",
             "attributes": attrs, "wkt": f"POINT({city['lon']} {city['lat']})"}
        n = get(NSRDB_URL, p, out, check_nsrdb)
        log(f"nsrdb {city['name']} {y}: {n}")
        res.append((y, n))
        time.sleep(1.0)
    return res


def fetch_power(city, outdir):
    tag = "" if (YEARS[0], YEARS[-1]) == (2019, 2023) else f"_{YEARS[0]}-{YEARS[-1]}"
    out = os.path.join(outdir, f"{city['name']}{tag}.json")
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return "skip"
    p = {"parameters": "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF",
         "community": "RE", "longitude": f"{float(city['lon']):.4f}",
         "latitude": f"{float(city['lat']):.4f}", "start": f"{YEARS[0]}0101",
         "end": f"{YEARS[-1]}1231", "format": "JSON", "time-standard": "UTC"}
    n = get(POWER_URL, p, out, check_power)
    log(f"power {city['name']}: {n}")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", default=os.path.join(ROOT, "raw/upstream/hedw-code/target_cities.csv"))
    ap.add_argument("--only", choices=["nsrdb", "power", "flags"],
                    help="flags: NSRDB ghi, clearsky_ghi, cloud_type, fill_flag into raw/nsrdb/flags/")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--years", default="2019-2023", help="first-last, e.g. 2011-2014 (default the HEDW-US period)")
    a = ap.parse_args()
    global YEARS
    y0, y1 = (int(v) for v in a.years.split("-"))
    YEARS = range(y0, y1 + 1)
    cities = list(csv.DictReader(open(a.cities)))[: a.limit]
    nd, pd_ = os.path.join(ROOT, "raw/nsrdb"), os.path.join(ROOT, "raw/power")
    os.makedirs(nd, exist_ok=True); os.makedirs(pd_, exist_ok=True)
    env = load_env()
    t0 = time.time()
    if a.only == "flags":
        fd = os.path.join(nd, "flags"); os.makedirs(fd, exist_ok=True)
        with ThreadPoolExecutor(a.workers) as ex:
            res = list(ex.map(lambda c: fetch_nsrdb(c, env, fd, FLAG_ATTRS, "_flags"), cities))
        bad = [(c["name"], y, n) for c, r in zip(cities, res) for y, n in r
               if not (n == "skip" or (isinstance(n, int) and n > 0))]
        log(f"flags done: {len(cities)*len(YEARS) - len(bad)}/{len(cities)*len(YEARS)} ok; failed: {bad}")
        log(f"elapsed {time.time()-t0:.0f} s")
        return
    if a.only != "nsrdb":
        with ThreadPoolExecutor(2) as ex:
            pres = list(ex.map(lambda c: fetch_power(c, pd_), cities))
        log(f"POWER done: {sum(1 for r in pres if r == 'skip' or (isinstance(r, int) and r > 0))}/{len(cities)} ok")
    if a.only != "power":
        with ThreadPoolExecutor(a.workers) as ex:
            nres = list(ex.map(lambda c: fetch_nsrdb(c, env, nd), cities))
        bad = [(c["name"], y, n) for c, r in zip(cities, nres) for y, n in r
               if not (n == "skip" or (isinstance(n, int) and n > 0))]
        log(f"NSRDB done: {len(cities)*len(YEARS) - len(bad)}/{len(cities)*len(YEARS)} ok; failed: {bad}")
    log(f"elapsed {time.time()-t0:.0f} s")


if __name__ == "__main__":
    sys.exit(main())

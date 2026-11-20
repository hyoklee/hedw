"""Show how HEDW-US's solar alignment resolves NSRDB :30 stamps onto the :00 master index.

02_build_dataset.py aligns with reindex(master_idx, method='nearest', tolerance='40min').
NSRDB GOES aggregated v4 at interval=60 stamps every record at minute 30, so every master
hour is equidistant (30 min) from two records. Run:
  uv run --no-project --python 3.11 --with pandas==2.3.3 python agent/checks/nearest_tie.py
"""
import pandas as pd

src = pd.Series([0, 1, 2], index=pd.to_datetime(
    ["2019-01-01 00:30", "2019-01-01 01:30", "2019-01-01 02:30"], utc=True))
master = pd.date_range("2019-01-01 00:00", "2019-01-01 03:00", freq="1h", tz="UTC")
out = src.reindex(master, method="nearest", tolerance=pd.Timedelta("40min"))
print("pandas", pd.__version__)
print(out)
# 00:00 -> record 00:30 (value 0): ties resolve to the LATER record.
assert list(out) == [0, 1, 2, 2]
print("master HH:00 holds the NSRDB record stamped HH:30 (+30 min)")

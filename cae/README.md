# cae/: clio-core CAE experiments on HEDW-US

The plan is to ingest only the columns an analysis needs, through OMNI `dataset_filter`s. CAE reads `hdf5` and `binary` but not CSV (clio-core `a23b96cbd`), so the steps are:

1. `hedw/csv_to_h5.py` converts each city CSV to `<city>.h5`, one 1-D dataset per column, with the units and time base as attributes.
2. `hedw/hedw_solar_omni.yaml` is an OMNI file whose `dataset_filter` keeps the timestamp and irradiance datasets. Everything else (demand, engineered features) is rejected.
3. `hedw/run_hedw.sh` runs `clio_run` + `clio_cae` and a verifier that checks byte-for-byte equality for the selected datasets and that rejected ones hold nothing.

The runtime configs and driver pattern are copied from `~/poro/cae/porotomo/` (single node, RAM tier). The results will go in `wiki/cae_omni_hedw_solar.md`.

Status: waiting for `raw/data.zip`.

#!/bin/bash
# OMNI run: step. NSRDB download CSVs start with two metadata lines (source,
# location id, units, ...) before the real header; drop them so the rest is a
# plain RFC 4180 table for the CAE csv:: assimilator.
# Usage (called by clio_cae): strip_nsrdb_header.sh <src.csv> <run_out.csv>
set -eu
tail -n +3 "$1" > "$2"

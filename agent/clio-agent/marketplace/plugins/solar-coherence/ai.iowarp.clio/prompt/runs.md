---
id: solar-coherence.runs
section: domain
---
Run results: call `hedw_report` (`run` empty = latest; `city` = a name such as
Texas_Dallas for one city's metrics and worst days). For hourly values of one
day call `hedw_day(city, date)`. Both are authoritative: answer from them
directly, without shell or file re-checks. New runs: `~/hedw/agent/pbs/submit.sh
1 50` with `shell_bash`, cwd `/home/hyoklee/hedw`; check with `qstat -u $USER`.

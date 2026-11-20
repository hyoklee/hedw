# Workflow: running the CLIO solar-coherence agent on Aurora

**Question:** with Aurora and the `IOWarp` allocation (debug queue), which workflow gets the most out of the CLIO agents (the detector, CAE ingest, clio-agent and clio-coder) for the HEDW-US coherence check?

## Measured stages (2026-11-20)

| Stage | Where | Nodes × ranks | Wall time | Node-hours charged | Throughput | Bottleneck |
|---|---|---|---|---|---|---|
| POWER download (150 cities × 5 y) | Login node, 2 threads | — | < 2 min | 0 | ~1.4 cities/s | Network |
| NSRDB download (750 city-years) | Login node, 3 threads | — | ~22 min (1,419 s with POWER) | 0 | ~0.55 files/s | API burst limit (HTTP 429), redirect to S3 |
| NSRDB fill flags (750) | Login node, 3 threads | — | *see log* | 0 | — | Same API |
| CAE bulk ingest, `csv::`, 9 of 16 columns, 746 files, 531 MB | Login node, single-node runtime (`cae/hedw/bulk_nsrdb.sh`) | 1 runtime | 7.86 s + 5.2 s header strip | 0 | 95 files/s, 67.5 MB/s | One `clio_cae` client; whole file parsed in memory |
| Detector, 149 cities | Login node, `run_local.sh` | 1 × P | 32.45 s (P=1) → 1.85 s (P=32) | 0 | 4.6 → 80 cities/s | Python start-up (0.46 s per process) and per-city work (~0.2 s) |
| Detector, 149 cities | Compute node, PBS 9107657, `debug` | 1 × 50 | 7.18 s detect + 2.90 s aggregate; job walltime 10 s; **queue wait 3 min 24 s** | 0.0028 (10 s) | 21 cities/s | Queue wait; cold reads of 1.2 GB of inputs from home (see below) |
| Detector, 149 cities | Compute node, PBS 9107666, `debug` | 1 × 16 | 7.43 s detect + 2.95 s aggregate; job walltime 11 s; **queue wait 2 min 51 s** | 0.0031 (11 s) | 20 cities/s | Same as 50 ranks: not rank count |
| clio-agent question | Login node → ALCF Minerva (Mistral Large 4) | — | median 2.2 s (benchmark); 20.6 s for a 5-tool open question | 0 | — | LLM round trips |
| clio-coder interpretation | Login node → ALCF Metis (gpt-oss-120b) | — | 16 s | 0 | — | One LLM turn |

### Detector strong scaling on the login node

`bench/results/local_scaling_aurora-uan-0012_20261120T143329Z.csv`:

| P | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| detect (s) | 32.45 | 14.88 | 7.97 | 4.29 | 2.59 | 1.85 | 1.95 |
| aggregate (s) | 1.68 | 1.37 | 1.35 | 1.39 | 1.34 | 1.29 | 1.29 |

Scaling is near-linear up to P = 8 and flattens beyond 16. The floor is roughly one city's work plus one Python start-up per process, about 0.67 s, as measured for Dallas.

**Compute node against login node.** Both debug jobs were about 2.5× slower to detect than the login node at P = 16: 7.18 s at 50 ranks and 7.43 s at 16. Rank count made no difference. The single-process aggregation step was 2.2× slower too (2.90–2.95 s against 1.34 s). The likely cause is that the compute node reads the 1.2 GB of NSRDB and POWER files cold from the home file system, while the login node had just downloaded them and holds them in page cache. Staging the inputs to node-local storage, or to `flare`, would be the fix if the job ever grows. All three runs produced a byte-identical `cities.csv`.

## Recommended workflow

1. **Login node: download.** NSRDB with at most 3 workers under the burst limit; POWER with 2 workers. Total ~25 min, 0 node-hours. Compute nodes would need the ALCF proxy and would just wait on the same API limit, so a PBS job here wastes allocation.
2. **Login node: detect and aggregate.** `agent/run_local.sh 16` takes about 4 s.
   - 149 cities × 5 years is **too small for a compute node**: the debug job's queue wait (3.4 min) is 50× the computation.
   - Use `agent/pbs/submit.sh` only when the work grows past what a login node should carry. Examples: the 13 GOES sub-hourly years, all ~2,000 NSRDB grid points in a metro, or Monte Carlo threshold studies.
   - Even then, use one node with ≤ 32 ranks and stage the inputs to node-local or `flare` storage first. On the compute node, 16 and 50 ranks took the same time.
3. **Optional CAE ingest.** Ingest the selected columns of all 745 files into CTE in under 8 s, when downstream tools should read through IOWarp instead of from CSVs. Don't run it on a node that hosts a clio-agent server; see the hazard below.
4. **LLM steps on the ALCF inference gateway**, which charges no Aurora node-hours.
   - **clio-agent** answers run questions in about 2 s through `hedw_report` and `hedw_day`.
   - **clio-coder** writes the narrative, and `check_numbers.py` plus a human review gate it.
   - The end-to-end loop is 4 s compute plus 2–20 s per question. The debug queue's one-job-per-user limit never comes into play.
5. **When compute nodes are needed:** use one `debug` job (≤ 2 nodes, ≤ 1 h, 1 job per user) that runs detection and aggregation together, as in `coherence.pbs`. Dependent jobs can't be queued in `debug`.

## Hazards found

- **clio-core tests kill clio-agent.**
  - **What happens:** `cr_pre_test_cleanup` and `cr_post_test_cleanup` in clio-core's ctest `kill -9` whatever holds ports 5555, 9413, … and every `clio_run` / `clio_daemon` process. Running the CAE test suite on the login node therefore killed the clio-agent server's embedded runtime, and the server answered 503 `ClioCoreRuntimeLostError` until it was restarted.
  - **Fix:** run clio-core tests on a different node or in a PBS job, or restart `agent/clio-agent/start.sh` afterwards.
  - **What is safe:** `clio_run stop --force` with its own port (10700) left the agent's runtime alone.
- **The debug queue** allows only one queued or running job per user. Use the login node for anything shorter than the queue wait.

## Related

[agent_solar_coherence.md](agent_solar_coherence.md) · [cae_csv_assimilator.md](cae_csv_assimilator.md) · [concept-data-access.md](concept-data-access.md)

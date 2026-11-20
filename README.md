# hedw

An [LLM wiki](llm-wiki.md) for **HEDW-US**, the Hourly Electricity Demand and Weather dataset for
141 major U.S. cities (2019–2023): M. Sleiman and R. Bo, "Descriptor: Hourly Electricity Demand and
Weather for Major U.S. Cities (2019–2023) Dataset (HEDW-US)", *IEEE Data Descriptions*, 2026,
[doi:10.1109/IEEEDATA.2026.3752026](https://doi.org/10.1109/IEEEDATA.2026.3752026) (CC BY 4.0).
Data: IEEE DataPort, [doi:10.21227/fpqq-nr70](https://doi.org/10.21227/fpqq-nr70) (CC BY 4.0).

The repo checks the dataset's solar irradiance against NASA POWER and runs it through
IOWarp's Context Assimilation Engine (clio-core CAE) and CLIO agents on Aurora.

- `wiki/`: the LLM-maintained knowledge base. Start at [wiki/index.md](wiki/index.md).
- `wiki/CLAUDE.md`: the schema the maintaining agent follows.
- `raw/`: immutable source metadata and small samples. The dataset zip is not committed.
- `cae/`: OMNI files, runtime configs and drivers for the CAE experiments.
- `agent/`: the solar-coherence anomaly agent (clio-agent and clio-coder), with run results.
- `bench/`: workflow-efficiency benchmarks on Aurora.
- `claude.md`: standing instructions for the agent working in this repo.
- `llm-wiki.md`: the pattern this repo follows.

Structure follows [hyoklee/poro](https://github.com/hyoklee/poro).

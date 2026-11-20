This repository is an LLM wiki (see llm-wiki.md) for paper [1].

Goals: document the dataset's structure, the science it supports,
and how IOWarp's Context Assimilation Engine (clio-core CAE) ingests it selectively
through OMNI files.

When testing clio-core, use the OMNI, configs and drivers under cae/ (see cae/README.md).
Record every ingest, query, and test run in wiki/log.md and keep wiki/index.md current.
Build an agent using clio-agent and clio-coder.

The agent identifies anomaly in solar radiatoin data.
Check  the solar radiation coherence for the experiment period in [1]
against ASDC POWER data/service [2].

Save all agent codes, scripts, and results in this wiki.

Find an optimal workflow that can maximize the efficiency of CLIO agents
given the Aurora's system and allocation.

Create a new `hedw` repo using my github.com account.
Keep commit and push changes as you make progress.


[1] https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=11781587
[2] https://power.larc.nasa.gov/ 
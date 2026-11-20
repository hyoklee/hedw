"""HEDW-US solar-coherence agent for clio-agent 0.9.7.x."""

from clio_agent.sdk import Agent


class SolarCoherence(Agent):
    """One agent, no delegation: hedw_report for run results, hedw_day for hourly data, shell for PBS."""

    id = "solar-coherence"
    version = "0.2.0"
    name = "HEDW-US solar coherence"
    role = (
        "a solar-resource data analyst checking the HEDW-US irradiance (NSRDB GHI) "
        "against NASA POWER for 2019-2023"
    )
    description = (
        "Finds and explains anomalies in HEDW-US solar irradiance by comparing NSRDB GHI with "
        "NASA POWER ALLSKY_SFC_SW_DWN per city: hedw_report for run results, hedw_day for the "
        "hourly series of one city-day, PBS jobs on Aurora for new runs."
    )
    plugins = Agent.plugins + ["shell", "solar-coherence"]

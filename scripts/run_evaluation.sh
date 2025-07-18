#!/bin/bash

run_id="set_run_id_here"

# if you want to use logfire set to true
use_logfire=false

if [ "$use_logfire" = true ]; then
    logfire_flag="--logfire"
else
    logfire_flag=""
fi

uv run -m web_agent_analyzer --run_id $run_id $logfire_flag
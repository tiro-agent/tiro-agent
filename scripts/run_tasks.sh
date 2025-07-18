#! /bin/bash

# set run id
run_id="set_run_id_here"

# if you want to use logfire set to true
use_logfire=false

if [ "$use_logfire" = true ]; then
    logfire_flag="--logfire"
else
    logfire_flag=""
fi

# first run the easy tasks
uv run -m web_agent \
--level easy \
--run-id $run_id \
$logfire_flag

# then run the medium tasks
uv run -m web_agent \
--level medium \
--run-id $run_id \
--disable-vpn-check \
$logfire_flag

# then run the hard tasks
uv run -m web_agent \
--level hard \
--run-id $run_id \
--disable-vpn-check \
$logfire_flag
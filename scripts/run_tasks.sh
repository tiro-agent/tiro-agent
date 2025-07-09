#! /bin/bash

# set run id
run_id="try_multi_screenshot_1"

uv run -m web_agent \
--logfire \
--level easy \
--run-id $run_id

uv run -m web_agent \
--logfire \
--level medium \
--run-id $run_id \
--disable-vpn-check

uv run -m web_agent \
--logfire \
--level hard \
--run-id $run_id \
--disable-vpn-check
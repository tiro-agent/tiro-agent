#! /bin/bash

# set run id
run_id="try_multi_screenshot_1"

# make sure the vpn is on, by prompting the user and he must reply "y"
read -p "Please turn on the vpn and reply 'y' to continue: "
if [ "$REPLY" != "y" ]; then
    echo "VPN is not on, please turn it on and run the script again"
    exit 1
fi

uv run -m web_agent \
--logfire \
--level easy \
--run-id $run_id \
--disable-vpn-check

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
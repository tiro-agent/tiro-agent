#! /bin/bash

model_name=o4-mini
run_dir="./output/run_id"

uv run -m web_judge.run \
    --model "${model_name}" \
    --trajectories_dir "$run_dir" \
    --output_path ${run_dir}/result \
    --num_worker 1 \
    --score_threshold 3

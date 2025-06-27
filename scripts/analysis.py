import json
import os
from pathlib import Path

run_id = '2025-06-24_01-44-52'
script_dir = Path(__file__).parent.resolve()
output_folder = (script_dir / '../output').resolve()

nr_success = 0
nr_failed_step_limit = 0
nr_failed_other = 0

for task in os.listdir(f'{output_folder}/{run_id}'):
	file_path = os.path.join(run_id, task, 'result.json')
	if os.path.exists(file_path):
		with open(file_path) as f:
			result = json.load(f)

			if 'ABORT' in result['final_result_response']:
				if 'step limit' in result['final_result_response']:
					nr_failed_step_limit += 1
				else:
					nr_failed_other += 1
					print(f'Task {task} failed with following reason: {result["final_result_response"]}')
			else:
				nr_success += 1

print(f'Statistics for run {run_id}:')
print(f'Number of successful tasks: {nr_success}')
print(f'Number of failed tasks: {nr_failed_step_limit + nr_failed_other}')
print(f'Number of failed tasks due to step limit: {nr_failed_step_limit}')
print(f'Number of failed tasks due to other reasons: {nr_failed_other}')
print(f'Accuracy: {nr_success / (nr_success + nr_failed_step_limit + nr_failed_other)}')
print(f'Accuracy (without unknown failures): {nr_success / (nr_success + nr_failed_step_limit)}')

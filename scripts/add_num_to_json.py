import json
import os


def add_num_to_json_data() -> None:
	with open('data/Online_Mind2Web.json') as f:
		data = json.load(f)

	for i, task in enumerate(data):
		task['number'] = i + 1
		task['task_id'] = task.pop('task_id')
		task['confirmed_task'] = task.pop('confirmed_task')
		task['website'] = task.pop('website')
		task['reference_length'] = task.pop('reference_length')
		task['level'] = task.pop('level')

	with open('data/Online_Mind2Web.json', 'w') as f:
		json.dump(data, f, indent=4)

	print('Done')


def add_num_to_json_output(run_id: str) -> None:
	for task_folder in os.listdir(f'output/{run_id}'):
		for file in os.listdir(f'output/{run_id}/{task_folder}'):
			if file.endswith('.json'):
				with open(f'output/{run_id}/{task_folder}/{file}') as f:
					data = json.load(f)
					data['number'] = int(task_folder.split('_')[0]) + 1

					data['task_id'] = data.pop('task_id')
					data['task'] = data.pop('task')
					data['level'] = data.pop('level')
					data['final_result_response'] = data.pop('final_result_response')
					data['action_history'] = data.pop('action_history')
					data['thoughts'] = data.pop('thoughts')

					print(json.dumps(data, indent=4))

				with open(f'output/{run_id}/{task_folder}/{file}', 'w') as f:
					json.dump(data, f, indent=4)

				# rename folder with correct number
				os.rename(f'output/{run_id}/{task_folder}', f'output/{run_id}/{data["number"]:03d}_{data["task_id"]}')


if __name__ == '__main__':
	# add_num_to_json_data()
	# add_num_to_json_output('try_threading_4')
	pass

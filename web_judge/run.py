import argparse
import asyncio
import copy
import json
import multiprocessing
import os
import re
from multiprocessing import synchronize

from dotenv import load_dotenv

from web_judge.methods.webjudge_online_mind2web import WebJudge_Online_Mind2Web_eval
from web_judge.utils import OpenaiEngine, extract_predication

load_dotenv()


def auto_eval(
	args: argparse.Namespace, task_subset: list[str], final_predicted_labels: list[int], lock: synchronize.Lock, model: OpenaiEngine
) -> None:
	# Get the already done task id
	output_json_path = os.path.join(args.output_path, f'Eval_{args.model}_score_threshold_{args.score_threshold}_auto_eval_results.json')
	already_ids = []
	if os.path.exists(output_json_path):
		with open(output_json_path) as f:
			already_data = f.read()
		already_tasks = already_data.splitlines()
		for item in already_tasks:
			item = json.loads(item)  # noqa
			already_ids.append(item['task_id'])

	print(f'The number of already done tasks: {len(already_ids)}')

	for task_id in task_subset:
		# Skip already done task
		if task_id in already_ids:
			continue

		# Load results
		with open(os.path.join(args.trajectories_dir, task_id, 'result.json')) as f:
			result = json.load(f)
			output_results = copy.deepcopy(result)
			task_description = result['task']
			action_history = result['action_history']

		# Load images
		screenshot_paths = []
		trajectory_images_path = os.path.join(args.trajectories_dir, task_id, 'trajectory')
		for image in sorted(os.listdir(trajectory_images_path), key=lambda x: int(re.findall(r'\d+', x)[0])):
			screenshot_paths.append(os.path.join(trajectory_images_path, image))

		print(f'Start evaluation for {task_description}')
		messages, text, system_msg, record, key_points = asyncio.run(
			WebJudge_Online_Mind2Web_eval(task_description, action_history, screenshot_paths, model, args.score_threshold)
		)

		output_results['image_judge_record'] = record
		output_results['key_points'] = key_points

		response = model.generate(messages)[0]
		predicted_label = extract_predication(response, 'Online_Mind2Web_eval')

		# Store evaluation details
		evaluation_results = {'response': response, 'predicted_label': predicted_label}
		output_results['task_id'] = task_id
		output_results['input_text'] = text
		output_results['system_msg'] = system_msg
		output_results['evaluation_details'] = evaluation_results
		output_results['predicted_label'] = predicted_label

		with lock:
			final_predicted_labels.append(predicted_label)

		print(f'Finish evaluation for {task_description}')
		print('=' * 20)
		os.makedirs(args.output_path, exist_ok=True)
		with lock:
			with open(
				os.path.join(args.output_path, f'Eval_{args.model}_score_threshold_{args.score_threshold}_auto_eval_results.json'),
				'a+',
			) as f_out:
				f_out.write(json.dumps(output_results) + '\n')


def process_subset(task_subset, args, final_predicted_labels, lock, model):  # noqa
	auto_eval(args, task_subset, final_predicted_labels, lock, model)


def parallel_eval(args: argparse.Namespace, num_workers: int = 3) -> None:
	# Evaluate in parallel based on num of works
	task_dirs = [d for d in sorted(os.listdir(args.trajectories_dir)) if os.path.isdir(os.path.join(args.trajectories_dir, d))]
	print(f'Evaluating {len(task_dirs)} tasks in total.')
	chunk_size = len(task_dirs) // num_workers
	task_subsets = [task_dirs[i : i + chunk_size] for i in range(0, len(task_dirs), chunk_size)]

	# Load model
	model = OpenaiEngine(model=args.model)

	lock = multiprocessing.Lock()
	with multiprocessing.Manager() as manager:
		final_predicted_labels = manager.list()
		processes = []
		for subset in task_subsets:
			p = multiprocessing.Process(target=process_subset, args=(subset, args, final_predicted_labels, lock, model))
			p.start()
			processes.append(p)

		for p in processes:
			p.join()

		success_num = sum(final_predicted_labels)

	print('Evaluation complete.')
	print(f'The success rate is {(success_num / len(task_dirs)) * 100}.')


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Auto evaluation of web navigation tasks.')
	parser.add_argument('--model', type=str, default='o4-mini')
	parser.add_argument('--trajectories_dir', type=str, required=True, help='Path to trajectories directory')
	parser.add_argument('--output_path', type=str, required=True, help='The output path')
	parser.add_argument(
		'--score_threshold',
		type=int,
		default=3,
		help='The score is a minimum threshold an image must achieve out of 5 to be considered relevant and included in the evaluation.',
	)
	parser.add_argument('--num_worker', type=int, default=3)
	args = parser.parse_args()

	parallel_eval(args, args.num_worker)

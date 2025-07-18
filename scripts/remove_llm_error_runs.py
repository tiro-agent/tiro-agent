import os
import shutil


def remove_errors_by_run_error_type(run_id: str, error_type: str, preview: bool = False) -> None:
	"""
	Remove tasks from a run by error type.

	For example, to remove all tasks with an LLM error, run:
		remove_errors_by_run_error_type('try_click_action_eval_v1', 'LLM_ERROR')
	"""
	output_dir = f'output/{run_id}'

	tasks = os.listdir(output_dir)

	for task in tasks:
		task_dir = os.path.join(output_dir, task)
		error_file_path = os.path.join(task_dir, 'error.txt')
		if os.path.exists(error_file_path):
			with open(error_file_path) as f:
				if error_type in f.read():
					print(f'Removing task {task} because it has an {error_type} error')
					if not preview:
						shutil.rmtree(task_dir)


def remove_errors_by_ai_eval_error_type(run_id: str, error_type: str, preview: bool = False) -> None:
	"""
	Remove tasks from a run by AI eval error type.

	For example, to remove all tasks with an human verification error, run:
		remove_errors_by_ai_eval_error_type('try_click_action_eval_v1', 'HUMAN_VERIFICATION_ERROR')
	"""
	output_dir = f'output/{run_id}'

	tasks = os.listdir(output_dir)

	for task in tasks:
		task_dir = os.path.join(output_dir, task)
		ai_eval_file_path = os.path.join(task_dir, 'ai.eval')
		if os.path.exists(ai_eval_file_path):
			with open(ai_eval_file_path) as f:
				if error_type in f.read():
					print(f'Removing task {task} because it has an {error_type} error')
					if not preview:
						shutil.rmtree(task_dir)


if __name__ == '__main__':
	preview = True
	run_id = 'try_click_action_eval_v1'

	remove_errors_by_run_error_type(run_id, 'LLM_ERROR', preview)
	remove_errors_by_run_error_type(run_id, 'LLM_ACTION_PARSING_ERROR', preview)
	remove_errors_by_run_error_type(run_id, 'URL_LOAD_ERROR', preview)

import os

from web_agent.agent.schemas import AgentErrors, SpecialRunErrors


def run(run_id: str) -> None:
	"""Auxiliary method to update the error types in the output folder to the newest format."""
	output_folder = f'output/{run_id}'
	all_task_runs = os.listdir(output_folder)

	for task_run in all_task_runs:
		if task_run == '#analysis' or task_run.startswith('.'):
			continue

		task_run_folder = os.path.join(output_folder, task_run)
		task_error_file = os.path.join(task_run_folder, 'error.txt')

		if not os.path.exists(task_error_file):
			continue

		with open(task_error_file) as f:
			task_error = f.read()
		print(task_error)

		if task_error == 'ACTION_PARSING_ERROR':
			with open(task_error_file, 'w') as f:
				f.write(SpecialRunErrors.LLM_ACTION_PARSING_ERROR.value)
		elif task_error == 'STEP_LIMIT_REACHED':
			with open(task_error_file, 'w') as f:
				f.write(SpecialRunErrors.STEP_LIMIT_ERROR.value)
		elif task_error == 'ABORTED_BY_LLM':
			with open(task_error_file, 'w') as f:
				f.write(SpecialRunErrors.LLM_ABORTED_ERROR.value)
		elif task_error == 'URL_BLOCKED':
			with open(task_error_file, 'w') as f:
				f.write(AgentErrors.PAGE_BLOCKED_ERROR.value)


if __name__ == '__main__':
	run('try_multi_screenshot_1')

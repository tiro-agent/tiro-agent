import os
import shutil


def remove_llm_error_runs(run_id: str, preview: bool = False) -> None:
	output_dir = f'output/{run_id}'

	tasks = os.listdir(output_dir)

	for task in tasks:
		task_dir = os.path.join(output_dir, task)
		if os.path.exists(os.path.join(task_dir, 'llm_error.txt')):
			print(f'Removing task {task} because it has an llm error')
			if not preview:
				shutil.rmtree(task_dir)


if __name__ == '__main__':
	remove_llm_error_runs('try_step_limit_25_temp_0_v1', False)

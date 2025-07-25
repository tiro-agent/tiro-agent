import os
import shutil


def remove_unfinished_tasks(run_id: str, preview: bool = False) -> None:
	"""
	Remove unfinished tasks from a run.

	Unfinished tasks are tasks that have no result.json file but have a trajectory folder.
	"""

	output_dir = f'output/{run_id}'

	tasks = os.listdir(output_dir)

	for task in tasks:
		task_dir = os.path.join(output_dir, task)

		if task == '#analysis':
			continue

		if not os.path.exists(os.path.join(task_dir, 'result.json')) and os.path.exists(os.path.join(task_dir, 'trajectory/')):
			print(f'Removing task {task} because it was not finished')
			if not preview:
				shutil.rmtree(task_dir)


if __name__ == '__main__':
	preview = True  # set to False to actually remove the tasks
	run_id = 'set_run_id_here'

	remove_unfinished_tasks(run_id, preview)

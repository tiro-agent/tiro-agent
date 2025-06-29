import json
import os
import sys
import time
from enum import Enum

from web_agent.agent.agent import Agent
from web_agent.agent.schemas import Task
from web_agent.browser.browser import Browser


class Level(Enum):
	"""
	Level of the task.

	There are 300 tasks in total.
	- Easy tasks: 83
	- Medium tasks: 143
	- Hard tasks: 74
	"""

	EASY = 'easy'
	MEDIUM = 'medium'
	HARD = 'hard'
	ALL = 'all'


class AgentRunner:
	def __init__(
		self,
		run_id: str | None = None,
		start_index: int = 0,
		relevant_task_ids: list[str] | None = None,
		output_dir_prefix: str | None = None,
	) -> None:
		self.run_id = run_id
		self.start_index = start_index
		self.tasks = []

		if self.run_id is None:
			self.run_id = time.strftime('%Y-%m-%d_%H-%M-%S')

		if output_dir_prefix is None:
			output_dir_prefix = 'output'

		self.output_dir = f'{output_dir_prefix}/{self.run_id}'

		with open('data/Online_Mind2Web.json') as f:
			self.tasks = json.load(f)
			if relevant_task_ids is not None:
				self.tasks = [t for t in self.tasks if t['task_id'] in relevant_task_ids]

			if self.start_index is not None and self.start_index > len(self.tasks):
				sys.exit('Start index is greater than the number of tasks')

	def run_all_tasks(self, level: Level = Level.ALL) -> None:
		for i, task in enumerate(self.tasks):
			if i < self.start_index:
				continue

			if level.value != Level.ALL.value and task['level'] != level.value:
				continue

			task_output_dir = f'{self.output_dir}/{i:03d}_{task["task_id"]}'

			if os.path.exists(task_output_dir):
				print(f'Task {i} already executed, skipping')
				continue

			task_object = Task(identifier=task['task_id'], description=task['confirmed_task'], url=task['website'])
			self.run_task(task_object, task_output_dir, i)

	def run_task_by_id(self, task_id: str) -> None:
		task = next((t for t in self.tasks if t['task_id'] == task_id), None)
		if task is None:
			sys.exit(f'Task with id {task_id} not found')

		task_output_dir = f'{self.output_dir}/{task["task_id"]}'
		task_object = Task(identifier=task['task_id'], description=task['confirmed_task'], url=task['website'])
		self.run_task(task_object, task_output_dir, 0)

	def run_task(self, task: Task, output_dir: str, nr: int) -> None:
		print(f'============= Task {nr} =============')
		print('Id:', task.identifier)
		print('Task:', task.description)
		print('Website:', task.url)

		with Browser() as browser:
			agent = Agent(browser)
			try:
				result = agent.run(task, output_dir=output_dir)
				print('Result:', result)
			except Exception as e:
				print(f'Task {nr} failed with following exception:', e)
		print('====================================\n\n')


def check_vpn() -> None:
	user_input = input("To avoid getting your IP blocked, it is recommended to use a VPN. Type 'y' to continue: ")
	while user_input.lower() != 'y':
		user_input = input("You did not confirm. Please type 'y' once your VPN is connected to continue: ")

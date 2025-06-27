import argparse
import json
import os
import sys
import time

import logfire
import nest_asyncio
from dotenv import load_dotenv

from web_agent.agent.agent import Agent
from web_agent.agent.schemas import Task
from web_agent.browser.browser import Browser

nest_asyncio.apply()
load_dotenv()


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

	def run_all_tasks(self) -> None:
		for i, task in enumerate(self.tasks):
			if i < self.start_index:
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


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Web Agent')
	parser.add_argument('--run-id', type=str, help='Run id', required=False, default=None)
	parser.add_argument('--start-index', type=int, help='Start index', required=False, default=0)
	parser.add_argument('--task-id', type=str, help='Task to perform (all if not given)', required=False, default=None)
	parser.add_argument('--relevant-task-ids', nargs='+', type=str, help='Relevant task ids', required=False, default=None)
	parser.add_argument('--logfire', action='store_true', help='Enable logfire logging', required=False, default=False)
	parser.add_argument('--disable-vpn-check', action='store_true', help='Disable VPN check', required=False, default=False)
	args = parser.parse_args()

	print('Hello from web-agent!')

	if not args.disable_vpn_check:
		check_vpn()

	if args.logfire:
		logfire.configure()
		logfire.instrument_pydantic_ai()

	# overwrite for testing
	# args.relevant_task_ids = ['824eb7bb0ef1ce40bfd49c12182d9428', 'e4e097222d13a2560db6f6892612dab6']

	runner = AgentRunner(
		run_id=args.run_id,
		relevant_task_ids=args.relevant_task_ids,
		start_index=args.start_index,
	)

	if args.task_id is None:
		runner.run_all_tasks()
	else:
		runner.run_task_by_id(args.task_id)

import asyncio
import json
import os
import sys
import time
from enum import Enum

from web_agent.agent.agent import Agent
from web_agent.agent.schemas import Task
from web_agent.browser.browser import Browser


class TaskLevel(Enum):
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
		self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
		self.gemini_api_key_2 = os.environ.get('GEMINI_API_KEY_2')

		if self.gemini_api_key is None:
			sys.exit('GEMINI_API_KEY is not set')

		self.api_key_queue = asyncio.Queue()
		self.api_key_queue.put_nowait(self.gemini_api_key)
		if self.gemini_api_key_2:
			self.api_key_queue.put_nowait(self.gemini_api_key_2)

		self.max_concurrent_tasks = self.api_key_queue.qsize()

		# Create semaphore to limit concurrency to number of API keys
		self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

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

		print(f'Runner initialized with max concurrent tasks (API keys): {self.max_concurrent_tasks}')

	async def run_all_tasks(self, level: TaskLevel = TaskLevel.ALL) -> None:
		filtered_tasks = []
		for task in self.tasks:
			if task['number'] < self.start_index:
				continue
			if level.value != TaskLevel.ALL.value and task['level'] != level.value:
				continue

			task_object = Task(
				identifier=task['task_id'],
				description=task['confirmed_task'],
				url=task['website'],
				level=task['level'],
				number=task['number'],
			)
			filtered_tasks.append(task_object)

		if not filtered_tasks:
			print('No tasks to run')
			return

		print(f'Running {len(filtered_tasks)} tasks with max {self.max_concurrent_tasks} concurrent tasks')

		# Run tasks in parallel using asyncio.gather
		if self.max_concurrent_tasks > 1:
			await asyncio.gather(*[self._run_task_with_api_key(task_data) for task_data in filtered_tasks])
		else:
			# Fallback to sequential execution if only one API key
			for task in filtered_tasks:
				await self._run_task_with_api_key(task)

	async def _run_task_with_api_key(self, task: Task) -> None:
		"""Run a single task with proper API key management."""

		task_output_dir = f'{self.output_dir}/{task.number:03d}_{task.identifier}'

		if os.path.exists(task_output_dir):
			print(f'Task {task.number} already executed, skipping')
			return

		# Acquire semaphore and get API key
		async with self.semaphore:
			api_key = await self.api_key_queue.get()
			try:
				await self.run_task(task, task_output_dir, api_key)
			finally:
				await self.api_key_queue.put(api_key)

	async def run_task_by_id(self, task_id: str) -> None:
		task = next((t for t in self.tasks if t['task_id'] == task_id), None)
		if task is None:
			sys.exit(f'Task with id {task_id} not found')

		task_output_dir = f'{self.output_dir}/{task["task_id"]}'
		task_object = Task(
			identifier=task['task_id'],
			description=task['confirmed_task'],
			url=task['website'],
			level=task['level'],
			number=task['number'],
		)
		await self.run_task(task_object, task_output_dir)

	async def run_task(self, task: Task, output_dir: str, api_key: str | None = None) -> None:
		print(f'============= Task {task.number} =============')
		print('Id:', task.identifier)
		print('Task:', task.description)
		print('Website:', task.url)

		async with Browser() as browser:
			agent = Agent(browser, api_key=api_key)
			try:
				result = await agent.run(task, output_dir=output_dir)
				print('Result:', result)
			except Exception as e:
				print(f'Task {task.number} failed with following exception:', e)
		print('====================================\n\n')


def check_vpn() -> None:
	user_input = input("To avoid getting your IP blocked, it is recommended to use a VPN. Type 'y' to continue: ")
	while user_input.lower() != 'y':
		user_input = input("You did not confirm. Please type 'y' once your VPN is connected to continue: ")

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
	"""
	Handles running the agent on all specified tasks, both sequentially and in parallel. Does NOT analyze results, this is handled by the
	separate web agent anaylizer.
	"""

	def __init__(  # noqa: PLR0913
		self,
		run_id: str | None = None,
		start_index: int = 0,
		relevant_task_ids: list[str] | None = None,
		relevant_task_numbers: list[int] | None = None,
		output_dir_prefix: str | None = None,
		step_factor: int = 2.5,
	) -> None:
		"""
		Initializes the AgentRunner with the specified parameters.

		:param run_id: The ID of the run, i.e. output folder name. If not provided, an ID based on the current time will be generated.
		:param start_index: The index of the task to start from. Default is 0.
		:param relevant_task_ids: A list of task IDs to run. If provided, `relevant_task_numbers` must be None.
		:param relevant_task_numbers: A list of task numbers to run. If provided, `relevant_task_ids` must be None.
		:param output_dir_prefix: The prefix for the output directory. If not specified, 'output' will be used.
		:param step_factor: The factor to determine the step limit. Default is 2.5.
		"""

		self.run_id = run_id
		self.start_index = start_index
		self.step_factor = step_factor
		self.tasks = []
		self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
		self.gemini_api_key_2 = os.environ.get('GEMINI_API_KEY_2')  # Adding a second API key enables parallel execution

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

		if relevant_task_numbers is not None and relevant_task_ids is not None:
			raise ValueError('Cannot use both relevant-task-numbers and relevant-task-ids')

		# Determine tasks to run
		with open('data/Online_Mind2Web.json') as f:
			self.tasks = json.load(f)
			if relevant_task_ids is not None:
				self.tasks = [t for t in self.tasks if t['task_id'] in relevant_task_ids]
			elif relevant_task_numbers is not None:
				self.tasks = [t for t in self.tasks if t['number'] in relevant_task_numbers]

			if self.start_index is not None and self.start_index > len(self.tasks):
				sys.exit('Start index is greater than the number of tasks')

		print(f'Runner initialized with max concurrent tasks (API keys): {self.max_concurrent_tasks}')

	async def run_all_tasks(self, level: TaskLevel = TaskLevel.ALL) -> None:
		"""
		Runs all tasks with the specified level.

		:param level: The level of tasks to run. Default is TaskLevel.ALL.
		"""
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
				reference_length=task['reference_length'],
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
		"""Runs a specific task by its ID."""
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
			reference_length=task['reference_length'],
		)
		await self.run_task(task_object, task_output_dir)

	async def run_task(self, task: Task, output_dir: str, api_key: str | None = None) -> None:
		"""Runs a specific task with the given API key."""
		print(f'============= Task {task.number} =============')
		print('Id:', task.identifier)
		print('Task:', task.description)
		print('Website:', task.url)
		print('Level:', task.level)

		step_limit = round(self.step_factor * task.reference_length)
		print('Step limit:', step_limit)

		async with Browser() as browser:
			agent = Agent(browser, api_key=api_key)
			try:
				result = await agent.run(task, output_dir=output_dir, step_limit=step_limit)
				print('Result:', result)
			except Exception as e:
				print(f'Task {task.number} failed with following exception:', e)
		print('====================================\n\n')


def check_vpn() -> None:
	"""Prompts the user to confirm active VPN connection."""
	user_input = input("To avoid getting your IP blocked, it is recommended to use a VPN. Type 'y' to continue: ")
	while user_input.lower() != 'y':
		user_input = input("You did not confirm. Please type 'y' once your VPN is connected to continue: ")

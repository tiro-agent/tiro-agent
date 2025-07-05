import json
import time
from pathlib import Path

from pydantic_ai import Agent as ChatAgent
from pydantic_ai import BinaryContent

from web_agent.agent.schemas import AgentErrors
from web_agent_analyzer.prompts import get_ai_eval_prompt
from web_agent_analyzer.schemas import Result, TaskErrorEvaluation


class ErrorEvaluator:
	"""
	Handles actual evaluation of an error using LLM.
	"""

	def __init__(self) -> None:
		self.llm: ChatAgent | None = None
		self._init_llm()

	def evaluate_task_error(self, task_result: Result, task_path: Path) -> AgentErrors | None:
		"""
		Evaluates the error type of a task using the LLM.
		"""
		prompt = self._get_task_prompt(task_path)
		task_error_evaluation = self._run_llm(prompt)

		print('-' * 100)
		print(f'Task number: {task_result.task_number}')
		print(task_error_evaluation.model_dump_json(indent=4))

		return task_error_evaluation.cause

	def _init_llm(self) -> None:
		"""
		Initializes the LLM agent.
		"""
		self.llm = ChatAgent(
			model='google-gla:gemini-2.5-flash-preview-05-20',
			system_prompt=get_ai_eval_prompt(),
			output_type=TaskErrorEvaluation,
		)

	def _run_llm(self, prompt: str | dict) -> TaskErrorEvaluation:
		"""
		Runs the LLM agent.
		"""
		max_retries = 4
		base_delay = 4

		for attempt in range(max_retries):
			try:
				response = self.llm.run_sync(prompt)
				return response.output
			except Exception as e:
				print(f'LLM call failed on attempt {attempt + 1}/{max_retries} with error: {e}')
				if attempt < max_retries - 1:
					delay = base_delay * (2**attempt)
					print(f'Reinitializing LLM and retrying in {delay} seconds...')
					time.sleep(delay)
					self._init_llm()
				else:
					print('Max retries reached. Failed to get a response from the LLM.')
					raise

	def _get_task_prompt(self, task_path: Path) -> list[str | BinaryContent]:
		"""
		Generates the prompt for the LLM evaluation of a task.
		"""
		with open(task_path / 'result.json') as f:
			task_result_json = json.load(f)

		screenshots_paths = sorted((task_path / 'trajectory').glob('*_full_screenshot.png'), key=lambda p: int(p.stem.split('_')[0]))
		screenshots = [open(screenshot_file, 'rb').read() for screenshot_file in screenshots_paths[-3:]]

		prompt_str = f'Task description: {task_result_json["task"]}\n'
		prompt_str += f'Steps performed: \n- {"\n- ".join(task_result_json["action_history"])}\n\n'
		prompt_str += f'Agent thoughts: \n- {"\n- ".join(task_result_json["thoughts"])}\n\n'

		return [
			prompt_str,
			'Screenshots:\n',
			*[BinaryContent(screenshot, media_type='image/png') for screenshot in screenshots],
		]

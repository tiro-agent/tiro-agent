import json
from pathlib import Path

from pydantic_ai import Agent as ChatAgent
from pydantic_ai import BinaryContent

from web_agent.agent.schemas import AgentErrors
from web_agent_analyzer.prompts import get_ai_eval_prompt
from web_agent_analyzer.schemas import Result, TaskErrorEvaluation


class ErrorEvaluator:
	def __init__(self) -> None:
		self.llm: ChatAgent | None = None
		self._init_llm()

	def evaluate_task_error(self, task_result: Result, task_path: Path) -> AgentErrors | None:
		prompt = self._get_task_prompt(task_path)
		task_error_evaluation = self._run_llm(prompt)

		print('-' * 100)
		print(f'Task number: {task_result.task_number}')
		print(task_error_evaluation.model_dump_json(indent=4))

		return task_error_evaluation.cause

	def _init_llm(self) -> ChatAgent:
		self.llm = ChatAgent(
			model='google-gla:gemini-2.5-flash-preview-05-20',
			system_prompt=get_ai_eval_prompt(),
			output_type=TaskErrorEvaluation,
		)

	def _run_llm(self, prompt: str | dict) -> TaskErrorEvaluation:
		response = self.llm.run_sync(prompt)
		return response.output

	def _get_task_prompt(self, task_path: Path) -> list[str | BinaryContent]:
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

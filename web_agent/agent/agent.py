import asyncio
import json
import math
import os

from pydantic_ai import Agent as ChatAgent
from pydantic_ai import BinaryContent
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.settings import ModelSettings

from web_agent.agent.actions.actions import ActionResult, ActionResultStatus
from web_agent.agent.actions.base import ActionContext
from web_agent.agent.actions.history import ActionsHistoryController, ActionsHistoryStep
from web_agent.agent.actions.registry import ActionsRegistry
from web_agent.agent.prompts import get_system_prompt
from web_agent.agent.schemas import AgentDecision, AgentErrors, SpecialRunErrors, Task
from web_agent.browser.browser import Browser

# These will be skipped immediatly to save time
KNOWN_PROBLEM_DOMAINS: list[dict[str, AgentErrors]] = [
	{'domain': 'https://www.gamestop.com/', 'reason': AgentErrors.PAGE_BLOCKED_ERROR},  # not immediately, but blocked by bot protection
	{'domain': 'https://www.kbb.com/', 'reason': AgentErrors.PAGE_BLOCKED_ERROR},  # not immediately, but blocked by bot protection
	{'domain': 'https://www.google.com/shopping?udm=28', 'reason': AgentErrors.HUMAN_VERIFICATION_ERROR},  # captcha after typing
	{'domain': 'https://seatgeek.com/', 'reason': AgentErrors.HUMAN_VERIFICATION_ERROR},  # blocked with captcha directly
	{'domain': 'https://doctor.webmd.com/', 'reason': AgentErrors.HUMAN_VERIFICATION_ERROR},  # blocked with captcha after clicking
	{'domain': 'https://www.thumbtack.com/', 'reason': AgentErrors.PAGE_LOAD_ERROR},  # return 404 permanently
]


class Agent:
	"""Implements the agent loop and basic logic, particularely the LLM integration."""

	MAX_ERROR_COUNT = 3  # Max number of LLM errors before task is aborted
	NUMBER_OF_PREVIOUS_SCREENSHOTS = 2  # Number of previous screenshots to feed into the LLM at each step

	def __init__(self, browser: Browser, api_key: str | None = None) -> None:
		self.browser = browser
		self.actions_controller = ActionsRegistry.create_default()
		self.action_history_controller = ActionsHistoryController()
		self.api_key = api_key

	async def run(self, task: Task, output_dir: str, step_limit: int = 20) -> str:  # noqa: PLR0915
		"""
		Run the agent on a given task.

		:param task: The task to run.
		:param output_dir: The directory to save the output.
		:param step_limit: The maximum number of steps to run.

		:return: The final output of the task.
		"""

		step = 0
		output_format_error_count = 0
		llm_error_count = 0
		previous_screenshots = []

		# STEP 0: Check if the domain is a known problem domain
		for known_problem_domain in KNOWN_PROBLEM_DOMAINS:
			if known_problem_domain['domain'] in task.url:
				return self._handle_error_finish(known_problem_domain['reason'], task, output_dir)

		# STEP 1: SETUP LLM
		llm = self._initialize_llm(task, self.api_key)

		# STEP 2: LOAD THE URL
		try:
			await self.browser.load_url(task.url)
		except Exception:
			return self._handle_error_finish(SpecialRunErrors.URL_LOAD_ERROR, task, output_dir)

		os.makedirs(output_dir + '/trajectory', exist_ok=True)

		# STEP 3: AGENT LOOP
		while True:
			# LOOP STEP 0: Check limits & errors and finish the task if needed
			if step >= step_limit:
				return self._handle_error_finish(SpecialRunErrors.STEP_LIMIT_ERROR, task, output_dir)

			# LOOP STEP 1: PAGE CLEANUP
			await self.browser.clean_page()

			# LOOP STEP 2: SAVE SCREENSHOT AND GET PAGE DATA
			screenshot_path = f'{output_dir}/trajectory/{step}_full_screenshot.png'
			screenshot = await self.browser.save_screenshot(screenshot_path)
			metadata = await self.browser.get_metadata()

			# LOOP STEP 3: GET AGENT PROMPT
			past_actions_str = self.action_history_controller.get_action_history_str()
			available_actions_str = await self.actions_controller.get_applicable_actions_str(self.browser.page)

			prompt = self._build_user_prompt(metadata, past_actions_str, available_actions_str, previous_screenshots, screenshot)

			print('-' * 100)
			print('Task:', task.number)
			print('Step number:', step)
			print('Metadata:', metadata)
			print('Past actions:\n', past_actions_str)

			# LOOP STEP 4: GET AGENT DECISION
			try:
				agent_response = await llm.run(prompt)
				action_decision: AgentDecision = agent_response.output
				print('Action: ', action_decision.action, ' - ', action_decision.thought)
			except Exception as e:
				print('Error getting action decision:', e)

				llm_error_count += 1
				if llm_error_count > self.MAX_ERROR_COUNT:
					print('Too many errors, aborting. Please check your API key and try again.')
					return self._handle_error_finish(SpecialRunErrors.LLM_ERROR, task, output_dir)

				await self._exponential_backoff(llm_error_count)
				llm = self._initialize_llm(task, self.api_key)
				continue

			llm_error_count = 0

			# LOOP STEP 5: ACTION PARSING
			try:
				action = self.actions_controller.parse_action_str(action_decision.action)
			except ValueError as e:
				print('Error parsing action:', e)

				# TODO: handle the error and reprompt the LLM including the error message

				output_format_error_count += 1
				if output_format_error_count > self.MAX_ERROR_COUNT:
					print('Too many errors, aborting')
					return self._handle_error_finish(SpecialRunErrors.LLM_ACTION_PARSING_ERROR, task, output_dir)
				print('Retrying...')
				continue

			output_format_error_count = 0

			# LOOP STEP 6: ACTION EXECUTION
			action_result = await action.execute(ActionContext(page=self.browser.page, task=task))
			self.action_history_controller.add_action(
				ActionsHistoryStep(
					thought=action_decision.thought,
					action=action,
					status=action_result.status,
					message=action_result.message,
					screenshot=screenshot_path,
				)
			)

			# LOOP STEP 7: TASK FINISHING
			if action_result.status in (ActionResultStatus.FINISH, ActionResultStatus.ABORT):
				return self._finish(task, action_result, output_dir)

			previous_screenshots.append(screenshot)

			# LOOP STEP 8: NEXT STEP
			await asyncio.sleep(3)
			step += 1

	def _handle_error_finish(self, error: SpecialRunErrors | AgentErrors, task: Task, output_dir: str) -> str:
		"""Handle a special error that the agent can encounter."""
		print(f'Handling special error: {error}')

		os.makedirs(output_dir, exist_ok=True)
		with open(f'{output_dir}/error.txt', 'w') as f:
			f.write(error.value)

		if error == SpecialRunErrors.LLM_ERROR:
			with open(f'{output_dir}/llm_error.txt', 'w') as f:
				f.write(error.value)

		return self._finish(
			task, ActionResult(status=ActionResultStatus.ERROR, message=f'Aborted due to following error: {error.value}'), output_dir
		)

	def _finish(self, task: Task, action_result: ActionResult, output_dir: str) -> str:
		"""Finish the task and write action history and result to a file."""
		with open(f'{output_dir}/action_history.txt', 'w') as f:
			f.write(f'Task description: {task.description}\n')
			f.write(f'Task url: {task.url}\n')
			f.write(f'Task output dir: {output_dir}\n')
			f.write(f'Action history: {self.action_history_controller.get_action_history_str()}\n')

		final_result = (
			action_result.data['answer'] if action_result.status == ActionResultStatus.FINISH else f'ABORTED: {action_result.message}'
		)

		if action_result.status == ActionResultStatus.ABORT:
			with open(f'{output_dir}/error.txt', 'w') as f:
				f.write(SpecialRunErrors.LLM_ABORTED_ERROR.value)

		output_data = {
			'number': task.number,
			'task_id': task.identifier,
			'task': task.description,
			'level': task.level,
			'final_result_response': final_result,
			'action_history': [step.action.get_action_str() for step in self.action_history_controller.get_action_history()],
			'thoughts': [step.thought for step in self.action_history_controller.get_action_history()],
		}
		with open(f'{output_dir}/result.json', 'w') as f:
			json.dump(output_data, f, indent=4)

		if action_result.status == ActionResultStatus.FINISH:
			print('Task finished with answer:', action_result.data['answer'])
		else:
			print('Task aborted with reason:', action_result.message)

		return final_result

	def _initialize_llm(self, task: Task, api_key: str | None = None) -> ChatAgent:
		"""Initialize the LLM with the task description."""
		system_prompt = get_system_prompt() + f'TASK: {task.description}'
		model_settings = ModelSettings(seed=42, temperature=0, timeout=20)

		# if api_key is not None, the key from os.environ.get('GEMINI_API_KEY') is used
		model_provider = GoogleGLAProvider(api_key=api_key)

		llm = ChatAgent(
			model='gemini-2.5-flash-preview-05-20',
			system_prompt=system_prompt,
			output_type=AgentDecision,
			model_settings=model_settings,
			model_provider=model_provider,
		)
		return llm

	async def _exponential_backoff(self, error_count: int) -> None:
		"""Exponential backoff to wait between errors."""
		seconds_to_wait = math.exp(error_count - 1) * 10  # 10 sec first error, 27 sec second error, 73 sec third error, etc.
		await asyncio.sleep(seconds_to_wait)
		print(f'Retrying in {seconds_to_wait} seconds...')

	def _build_user_prompt(
		self,
		metadata: dict,
		past_actions_str: str,
		available_actions_str: str,
		previous_screenshots: list[str],
		current_screenshot: str,
	) -> list[BinaryContent | str]:
		"""
		Build the user prompt for the LLM.

		:param metadata: Metadata about the task.
		:param past_actions_str: String representation of the past actions.
		:param available_actions_str: String representation of all currently available actions.
		:param previous_screenshots: List of previous screenshots.
		:param current_screenshot: Current screenshot.

		:return: List of BinaryContent or str representing the user prompt.
		"""
		prompt_str = '\n'
		prompt_str += f'Metadata: \n{metadata!s}\n\n'
		prompt_str += f'Past actions:\n{past_actions_str}\n\n'
		prompt_str += f'Available actions:\n{available_actions_str}\n\n'
		prompt_str += 'Choose the next action to take.\n'

		if len(previous_screenshots) > 0:
			screenshots_to_include = previous_screenshots[-self.NUMBER_OF_PREVIOUS_SCREENSHOTS :]
			prompt = [
				prompt_str,
				'Previous screenshots:',
				*[BinaryContent(data=screenshot, media_type='image/png') for screenshot in screenshots_to_include],
				'Current screenshot:',
				BinaryContent(data=current_screenshot, media_type='image/png'),
			]
		else:
			prompt = [
				prompt_str,
				'Current screenshot:',
				BinaryContent(data=current_screenshot, media_type='image/png'),
			]

		return prompt

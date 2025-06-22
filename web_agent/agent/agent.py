import json
import math
import sys
import time

from pydantic_ai import Agent as ChatAgent
from pydantic_ai import BinaryContent
from pydantic_ai.settings import ModelSettings

from web_agent.agent.actions.actions import ActionResult, ActionResultStatus
from web_agent.agent.actions.history import ActionsHistoryController, ActionsHistoryStep
from web_agent.agent.actions.registry import ActionsRegistry
from web_agent.agent.prompts import get_system_prompt
from web_agent.agent.schemas import AgentDecision, Task
from web_agent.browser.browser import Browser


class Agent:
	MAX_ERROR_COUNT = 3

	def __init__(self, browser: Browser) -> None:
		self.browser = browser
		self.actions_controller = ActionsRegistry.create_default()
		self.action_history_controller = ActionsHistoryController()
		self.system_prompt = get_system_prompt()

	def run(self, task: Task, max_steps: int = 20) -> str:  # noqa: PLR0915
		step = 0
		output_format_error_count = 0
		llm_error_count = 0

		# STEP 0: SETUP LLM
		system_prompt = self.system_prompt + f'TASK: {task.description}'
		llm = initialize_llm(system_prompt)

		# STEP 1: LOAD THE URL
		self.browser.load_url(task.url)

		# STEP 2: AGENT LOOP
		while True:
			# LOOP STEP 1: PAGE CLEANUP
			self.browser.clean_page()
			# TODO: add actual cleanup

			# LOOP STEP 2: GET PAGE DATA
			screenshot_path = f'{task.output_dir}/{step}_full_screenshot.png'
			screenshot = self.browser.save_screenshot(screenshot_path)
			metadata = self.browser.get_metadata()
			print('Metadata:', metadata)

			# LOOP STEP 3: PAGE ANALYSIS
			# TODO

			# LOOP STEP 4: MULTISTEP PLANNING
			# TODO

			# LOOP STEP 5: GET AGENT PROMPT
			past_actions_str = self.action_history_controller.get_action_history_str()
			available_actions_str = self.actions_controller.get_applicable_actions_str(self.browser.page)

			prompt_str = '\n'
			prompt_str += f'Metadata: \n{metadata!s}\n\n'
			prompt_str += f'Past actions:\n{past_actions_str}\n\n'
			prompt_str += f'Available actions:\n{available_actions_str}\n\n'
			prompt_str += 'Choose the next action to take.\n'

			prompt = [
				BinaryContent(data=screenshot, media_type='image/png'),
				prompt_str,
			]

			print('-' * 100)
			print('Step number:', step)
			print('Metadata:', metadata)
			print('Past actions:\n', past_actions_str)

			# LOOP STEP 6: GET AGENT DECISION
			try:
				action_decision: AgentDecision = llm.run_sync(prompt).output
				print('Action: ', action_decision.action, ' - ', action_decision.thought)
			except Exception as e:
				print('Error getting action decision:', e)

				llm_error_count += 1
				if llm_error_count > self.MAX_ERROR_COUNT:
					print('Too many errors, aborting. Please check your API key and try again.')
					sys.exit()

				llm = initialize_llm(system_prompt)
				print('Re-initializing LLM')

				seconds_to_wait = math.exp(llm_error_count - 1) * 10  # 10 sec first error, 27 sec second error, 73 sec third error, etc.
				print(f'Retrying in {seconds_to_wait} seconds...')
				time.sleep(seconds_to_wait)
				continue

			llm_error_count = 0

			# LOOP STEP 7: ACTION PARSING
			try:
				action = self.actions_controller.parse_action_str(action_decision.action)
			except ValueError as e:
				print('Error parsing action:', e)

				# TODO: handle the error and reprompt the LLM including the error message

				output_format_error_count += 1
				if output_format_error_count > self.MAX_ERROR_COUNT:
					print('Too many errors, aborting')
					break
				print('Retrying...')
				continue

			output_format_error_count = 0

			# LOOP STEP 8: ACTION EXECUTION
			action_result = action.execute(self.browser.page, task)
			self.action_history_controller.add_action(
				ActionsHistoryStep(
					thought=action_decision.thought,
					action=action,
					status=action_result.status,
					message=action_result.message,
					screenshot=screenshot_path,
				)
			)

			if step >= max_steps:
				action_result = ActionResult(status=ActionResultStatus.ABORT, message='step limit reached')

			# LOOP STEP 9: TASK FINISHING
			if action_result.status in (ActionResultStatus.FINISH, ActionResultStatus.ABORT):
				# dump the action history to a file
				with open(f'{task.output_dir}/action_history.txt', 'w') as f:
					f.write(f'Task description: {task.description}\n')
					f.write(f'Task url: {task.url}\n')
					f.write(f'Task output dir: {task.output_dir}\n')
					f.write(f'Action history: {self.action_history_controller.get_action_history_str()}\n')

				final_result = (
					action_result.data['answer']
					if action_result.status == ActionResultStatus.FINISH
					else f'ABORTED: {action_result.message}'
				)

				output_data = {
					'task_id': task.identifier,
					'task': task.description,
					'final_result_response': final_result,
					'action_history': [step.action.get_action_str() for step in self.action_history_controller.get_action_history()],
					'thoughts': [step.thought for step in self.action_history_controller.get_action_history()],
				}
				with open(f'{task.output_dir}/result.json', 'w') as f:
					json.dump(output_data, f, indent=4)

				if action_result.status == ActionResultStatus.FINISH:
					print('Task finished with answer:', action_result.data['answer'])
				else:
					print('Task aborted with reason:', action_result.message)

				return final_result

			# LOOP STEP 10: SELF-REVIEW
			# evaluate the step success (look at pre and after screenshots) and the agent's performance & ADD A NOTE to the action history
			# TODO

			# LOOP STEP 11: NEXT STEP
			time.sleep(3)
			step += 1


def initialize_llm(system_prompt: str) -> ChatAgent:
	model_settings = ModelSettings(seed=42, temperature=0, timeout=20)
	llm = ChatAgent(
		model='google-gla:gemini-2.5-flash-preview-05-20',
		system_prompt=system_prompt,
		output_type=AgentDecision,
		model_settings=model_settings,
	)
	return llm

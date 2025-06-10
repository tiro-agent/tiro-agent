import time

from pydantic_ai import Agent as ChatAgent
from pydantic_ai import BinaryContent

from web_agent.agent.actions import (
	ActionDecision,
	ActionHistoryController,
	ActionHistoryStep,
	ActionResultStatus,
	ActionsController,
)
from web_agent.agent.prompts import get_system_prompt
from web_agent.agent.schema import Task
from web_agent.browser.browser import Browser


class Agent:
	MAX_ERROR_COUNT = 3

	def __init__(self, browser: Browser) -> None:
		self.browser = browser
		self.actions_controller = ActionsController.create_default()
		self.action_history_controller = ActionHistoryController()
		self.system_prompt = get_system_prompt()

	def run(self, task: Task) -> None:  # noqa: PLR0915
		step = 0
		output_format_error_count = 0
		llm_error_count = 0

		# STEP 0: SETUP LLM
		system_prompt = self.system_prompt + f'TASK: {task.description}'
		llm = ChatAgent(model='google-gla:gemini-2.5-flash-preview-05-20', system_prompt=system_prompt, output_type=ActionDecision)

		# STEP 1: LOAD THE URL
		self.browser.load_url(task.url)

		# STEP 2: AGENT LOOP
		while True:
			# LOOP STEP 1: PAGE CLEANUP
			self.browser.clean_page()
			# TODO: add actual cleanup

			# LOOP STEP 2: GET PAGE DATA
			screenshot_path = f'{task.output_dir}/step_{step}.png'
			screenshot = self.browser.save_screenshot(screenshot_path)
			metadata = self.browser.get_metadata()

			# LOOP STEP 3: PAGE ANALYSIS
			# TODO

			# LOOP STEP 4: MULTISTEP PLANNING
			# TODO

			# LOOP STEP 5: GET AGENT PROMPT
			past_actions_str = self.action_history_controller.get_action_history_str()
			available_actions_str = self.actions_controller.get_applicable_actions_str(self.browser.page)

			prompt_str = '\n'
			# prompt_str += f'Metadata: \n{metadata!s}\n\n'
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
				action_decision: ActionDecision = llm.run_sync(prompt).output
				print('Action: ', action_decision.action, ' - ', action_decision.thought)
			except Exception as e:
				print('Error getting action decision:', e)

				llm_error_count += 1
				if llm_error_count > self.MAX_ERROR_COUNT:
					print('Too many errors, aborting. Please try again.')
					break
				print('Retrying...')
				time.sleep(3)
				continue

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
				ActionHistoryStep(action=action, status=action_result.status, message=action_result.message, screenshot=screenshot_path)
			)

			if action_result.status in (ActionResultStatus.FINISH, ActionResultStatus.ABORT):
				print('Task finished with status:', action_result.status)

				# dump the action history to a file
				with open(f'{task.output_dir}/action_history.txt', 'w') as f:
					f.write(f'Task description: {task.description}\n')
					f.write(f'Task url: {task.url}\n')
					f.write(f'Task output dir: {task.output_dir}\n')
					f.write(f'Action history: {self.action_history_controller.get_action_history_str()}\n')

				break

			time.sleep(3)
			step += 1

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

"""
The new agent implementation would be as follows:

1. The agent would be a class with a run method.
2. The class would have a browser instance, a system prompt, and an actions controller.
3. The run method would take a task, a url, and an output directory.
4. The run method would load the url. (call browser.load_url(url))
5. The run method would start the agent loop:
	- save a screenshot of the page. (call browser.save_screenshot(f'{output_dir}/step_{step}.png'))
	- clean the page. (call browser.clean_page())
	- generate a prompt for the LLM. (call generate_step_prompt())
	- generate the agent instance. (call _generate_llm_with_actions(page, system_prompt, actions_controller))
	- run the agent. (call agent.run_sync())
	- get the LLM's response (automatically parsed by pydantic_ai)
	- execute the action
	- save the action to the action history including the result, message, the action itself, page_metadata, and the screenshot
	- sleep for 5 seconds
	- if ActionResult.status is not FINISH or ABORT, go back to step 5
	- if ActionResult.status is FINISH, return the answer
	- if ActionResult.status is ABORT, return the answer

- log all the steps and actions, and the results of the actions
- log the final answer
- output the logging to the console
"""

MAX_ERROR_COUNT = 3


class Agent:
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
				if llm_error_count > MAX_ERROR_COUNT:
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
				if output_format_error_count > MAX_ERROR_COUNT:
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

import json
import time

from playwright.sync_api import Page
from pydantic_ai import Agent as ChatAgent
from pydantic_ai import BinaryContent

from web_agent.agent.actions import ActionHistoryController, ActionHistoryStep, ActionResultStatus, ActionsController
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


class Agent:
	def __init__(self, browser: Browser) -> None:
		self.browser = browser
		self.actions_controller = ActionsController.create_default()
		self.action_history_controller = ActionHistoryController()
		self.system_prompt = get_system_prompt()

	def run(self, task: Task) -> None:
		step = 0

		self.system_prompt = self.system_prompt + f'TASK: {task.description}'
		print(self.system_prompt)
		self.browser.load_url(task.url)

		# AGENT LOOP
		while True:
			# PAGE LOADING AND CLEANUP
			# Page already loaded at start or through action
			self.browser.clean_page()
			screenshot_path = f'{task.output_dir}/step_{step}.png'
			self.browser.save_screenshot(screenshot_path)
			screenshot = open(screenshot_path, 'rb').read()
			metadata = self.browser.get_metadata()
			print('Metadata:', metadata)
			# TODO: add cleanup

			# PAGE ANALYSIS
			# TODO

			# PAGE AND TASK EVALUATION / MULTISTEP PLANNING - TODO: separate
			past_actions_str = self.action_history_controller.get_action_history_str()
			print(past_actions_str)

			llm = _generate_llm_with_actions(self.browser.page, self.system_prompt, self.actions_controller)

			available_actions_str = self.actions_controller.get_applicable_actions_str(self.browser.page)
			print('Available actions:', available_actions_str, '\n', '=' * 100)

			prompt = [
				'AVAILABLE ACTIONS:\n' + available_actions_str,
				#'NEXT STEP, CHOOSE ACTION\n\n',
				#'Metadata: \n',
				# str(metadata),
				BinaryContent(data=screenshot, media_type='image/png'),
				past_actions_str,
			]

			action_decision = llm.run_sync(prompt).output
			print('Action: ', action_decision.action.get_action_str(), ' - ', action_decision.thought)

			# STEP EXECUTION
			action = action_decision.action
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

			time.sleep(5)
			step += 1


def _generate_llm_with_actions(
	page: Page,
	system_prompt: str,
	actions_controller: ActionsController,
	model: str = 'google-gla:gemini-2.5-flash-preview-05-20',
) -> ChatAgent:
	agent_decision_type = actions_controller.get_agent_decision_type(page)
	print('Agent decision type:', json.dumps(agent_decision_type.model_json_schema(), indent=2))
	llm = ChatAgent(model, system_prompt=system_prompt, output_type=agent_decision_type)
	return llm

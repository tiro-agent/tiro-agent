import time

from agent.prompts import get_possible_actions_prompt, get_system_prompt
from browser.browser import Browser
from pydantic_ai import Agent as ChatAgent
from pydantic_ai import BinaryContent


class Agent:
	def __init__(self, browser: Browser) -> None:
		self.browser = browser
		possible_actions = get_possible_actions_prompt()
		self.system_prompt = get_system_prompt(possible_actions)

	def run(self, task: str, url: str, output_dir: str) -> None:
		step = 0
		past_actions = []

		self.system_prompt = self.system_prompt + f'TASK: {task}'
		print(self.system_prompt)
		llm = ChatAgent('google-gla:gemini-2.5-flash-preview-05-20', system_prompt=self.system_prompt)

		self.browser.load_url(url)

		# AGENT LOOP
		while True:
			# PAGE LOADING AND CLEANUP
			# Page already loaded at start or through action
			self.browser.clean_page()
			self.browser.save_screenshot(f'{output_dir}/step_{step}.png')
			screenshot = open(f'{output_dir}/step_{step}.png', 'rb').read()
			# html = self.browser.get_html()
			metadata = self.browser.get_metadata()
			print('Metadata:', metadata)
			# TODO: add cleanup

			# PAGE ANALYSIS
			# TODO

			# PAGE AND TASK EVALUATION / MULTISTEP PLANNING - TODO: separate
			past_actions_str = 'Prior actions: \n- ' + '\n- '.join(
				[f'ACTION: {action}, SUCCESS: {"n/a" if success is None else success}' for (action, success, message) in past_actions]
			)
			print(past_actions_str)

			action = (
				llm.run_sync(
					[
						#'NEXT STEP, CHOOSE ACTION\n\n',
						#'Metadata: \n',
						# str(metadata),
						BinaryContent(data=screenshot, media_type='image/png'),
						past_actions_str,
					]
				)
				.output.strip()
				.replace('"', "'")
			)
			print('Action:', action)

			# STEP EXECUTION
			command, args = action.split("('")[0], action.split("('")[1].split("')")[0].replace("', '", "','").split("','")
			print('Command:', command)
			print('Args:', args)

			success = None
			message = ''
			if command == 'click_text':
				success, message = self.browser.click_by_text(args[0])
			elif command == 'scroll':
				self.browser.page.mouse.wheel(0, 700 if args[0] == 'down' else -700)
				success = None
			elif command == 'search':
				success, message = self.browser.search_and_highlight(args[0])
			elif command == 'fill':
				self.browser.fill_closest_input_to_text(args[0], args[1])
			elif command == 'return':
				return args[0]
			elif command == 'click_coord':
				self.browser.page.mouse.click(int(args[0]), int(args[1]))
				success = None
			elif command == 'type':
				self.browser.page.keyboard.type(args[0])
				success = None
			elif command == 'back':
				self.browser.page.evaluate('window.history.back()')
				success = None
			elif command == 'reset':
				self.browser.load_url(url)
				success = None

			print('Success:', success)
			print('Message:', message)

			time.sleep(5)
			step += 1
			past_actions.append((action, success, message))

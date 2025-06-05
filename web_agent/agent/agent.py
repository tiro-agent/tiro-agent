import time

from browser.browser import Browser
from pydantic_ai import Agent as ChatAgent
from pydantic_ai import BinaryContent


class Agent:
	def __init__(self, browser: Browser):
		self.browser = browser

		possible_actions = """
		- "click_text('text')": Click on the first element that contains the given text.
		- "click_coord('x', 'y')": Click on the element at the given coordinates.
		- "scroll('direction')": Scroll the page in the given direction. Valid directions are 'up', 'down'.
		- "search('query')": Search for the given query on the current page and focus on it.
		- "type('text')": Type the given text into the focused element.
		- "back('')": Go back to the previous page.
		- "reset('')": Reset the browser to the initial starting page.
		"""

		# BACKUP FOR EASY COPYING
		backup = """
		- "scroll('direction')": Scroll the page in the given direction. Valid directions are 'up', 'down'.
		- "fill('placeholder', 'input')": Fill the given input text into the first element that has the given placeholder text.
		"""

		self.system_prompt = f"""
		You are a web agent. You will be given a task that you must complete. Do always verify that you are working towards that task.

		At each step, you will be given a screenshot of the current page alongside some metadata. Use this information to determine what action to take next.
		You will also be given a list of past actions that you have taken as well as their results.

		These are all possible actions:
		{possible_actions}

		Only output exactly one action. Do not output anything else.
		ONLY WHEN you have FULLY performed the task, output "return('result')" with the requested information. Be as concise as possible.
		DO NOT TAKE THE SAME ACTION MORE THAN TWICE IN A ROW.

		"""

	def run(self, task, url, output_dir):
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
				[
					f'ACTION: {action}, SUCCESS: {"n/a" if success is None else success}'
					for (action, success, message) in past_actions
				]
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

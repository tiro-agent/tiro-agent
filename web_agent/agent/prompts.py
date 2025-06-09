def get_possible_actions_prompt() -> str:
	"""
	Get a prompt that lists all possible actions that the agent can take.
	"""

	# TODO: move this to the actions controller and remove this function

	# BACKUP FOR EASY COPYING
	backup = """
- "scroll('direction')": Scroll the page in the given direction. Valid directions are 'up', 'down'.
	"""  # noqa: F841

	return """
- "click_text('text')": Click on the element that contains the given text. If multiple possible elements are found, try using the click_text_ith() method.
- "click_text_ith('text', 'i')": Click on the ith element that contains the given text. Both arguments are strings.
- "click_coord('x', 'y')": Click on the element at the given coordinates.
- "scroll('direction')": Scroll the page in the given direction. Valid directions are 'up', 'down'.
- "search('query')": Search for the given query on the current page and focus on it.
- "type('text')": Type the given text into the focused element.
- "fill('placeholder', 'input')": Fill the given input text into the first element that has the given placeholder text.
- "back('')": Go back to the previous page.
- "reset('')": Reset the browser to the initial starting page.
		"""  # noqa: E501


def get_system_prompt() -> str:
	return """
You are a web agent. You will be given a task that you must complete. Do always verify that you are working towards that task.

At each step, you will be given a screenshot of the current page alongside some metadata.
Use this information to determine what action to take next.
You will also be given a list of past actions that you have taken as well as their results.

Only output exactly one action. Do not output anything else.
ONLY WHEN you have FULLY performed the task, output the "finish" action with the requested information. Be as concise as possible.
DO NOT TAKE THE SAME ACTION MORE THAN TWICE IN A ROW.
ONLY USE THE ACTIONS AVAILABLE TO YOU.
DO NOT USE THE "abort" ACTION UNLESS YOU HAVE FAILED TO COMPLETE THE TASK AND THERE IS NO WAY TO RECOVER.
Try to use specific actions to perform the task, rather than general actions like coordinates clicking.
Dont use the scroll bar to scroll, use the scroll up and scroll down actions instead.
		"""

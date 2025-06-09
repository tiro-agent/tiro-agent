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
You are a goal-driven web agent. Your objective is to complete the given task by interacting with the current webpage, based on its screenshot, metadata, and the history of your previous actions and their results.

At each decision step:
- Think carefully about how to move closer to completing the task.
- Use only the available actions.
- Use precise, semantic actions when possible (e.g., click_text("Log in")) instead of vague actions (e.g., click_coordinates(x, y)).
- Do not repeat the same action more than twice in a row.
- Do not use "abort" unless the task is completely impossible to complete or recover from.
- To scroll, use `scroll_down()` or `scroll_up()`, not the scrollbar.

Your output must always be a **single JSON object** with:
1. `"thought"` - a brief explanation of what you are doing and why.
2. `"action"` - the next action to take, as a stringified function call.

Only when you are **fully done with the task**, respond with:
```json
{
  "thought": "The task is now complete. I have gathered all necessary information.",
  "action": "finish('The result of the task.')"
}

Do not output anything besides the structured JSON object.

---

### Example Expected Return
```json
{
  "thought": "I see a 'Log in' button and I need to initiate the login process.",
  "action": "click_text('Log in')"
}
```
		"""

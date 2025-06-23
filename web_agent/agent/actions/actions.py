from playwright._impl._errors import TimeoutError
from playwright.async_api import Page
from pydantic import Field

from web_agent.agent.actions.base import ActionContext, ActionResult, ActionResultStatus, BaseAction, default_action
from web_agent.browser.browser import pretty_print_element

# @default_action
# class Click(BaseAction):
# 	"""Clicks a specific element on the page."""

# 	selector: str = Field(description='The selector to click on.')

# 	def execute(self, context: ActionContext) -> ActionResult:
# 		targets = context.page.get_by_text(self.selector).filter(visible=True)
# 		if targets.count() == 0:
# 			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
# 		elif targets.count() == 1:
# 			targets.click()
# 			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the first element that contains the given text.')
# 		else:
# 			return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple targets found: ' + str(targets.all()))


@default_action
class ClickByText(BaseAction):
	"""Clicks the element that contains the given text. Will respond with all options if multiple candidates are found. If no elements are found, it tries looking for subtexts."""

	text: str = Field(description='The text to click on.')

	def execute(self, context: ActionContext) -> ActionResult:
		text_targets = context.page.get_by_text(self.text).filter(visible=True)
		placeholder_targets = context.page.get_by_placeholder(self.text).filter(visible=True)
		label_targets = context.page.get_by_label(self.text).filter(visible=True)
		targets = text_targets.or_(placeholder_targets).or_(label_targets)

		if targets.count() == 0:  # If no targets found, try to find subtexts
			for subtext in self.text.split():
				text_subtargets = context.page.get_by_text(subtext).filter(visible=True)
				placeholder_subtargets = context.page.get_by_placeholder(subtext).filter(visible=True)
				label_subtargets = context.page.get_by_label(subtext).filter(visible=True)
				subtext_targets = text_subtargets.or_(placeholder_subtargets).or_(label_subtargets)
				if subtext_targets.count() > 0:
					targets = targets.or_(subtext_targets)

		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() == 1:
			try:
				targets.click()
			except TimeoutError:
				return ActionResult(status=ActionResultStatus.FAILURE, message='Click timed out, element might not be clickable')
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the element that contains the given text.')
		else:
			targets_str = str([f'{i} -  {pretty_print_element(target.element_handle())}' for i, target in enumerate(targets.all())])
			return ActionResult(
				status=ActionResultStatus.FAILURE,
				message='Multiple targets found: '
				+ targets_str
				+ '\n\nPlease specify the index of the element to click on using the ClickByTextIth action.',
			)


@default_action
class ClickByTextIth(BaseAction):
	"""Clicks on the ith element that contains the given text."""

	text: str = Field(description='The text to click on.')
	ith: int = Field(description='The index of the element to click on. Starts at 0, so 0 is the first element.')

	def execute(self, context: ActionContext) -> ActionResult:
		text_targets = context.page.get_by_text(self.text).filter(visible=True)
		placeholder_targets = context.page.get_by_placeholder(self.text).filter(visible=True)
		label_targets = context.page.get_by_label(self.text).filter(visible=True)
		targets = text_targets.or_(placeholder_targets).or_(label_targets)

		if targets.count() == 0:  # If no targets found, try to find subtexts
			for subtext in self.text.split():
				text_subtargets = context.page.get_by_text(subtext).filter(visible=True)
				placeholder_subtargets = context.page.get_by_placeholder(subtext).filter(visible=True)
				label_subtargets = context.page.get_by_label(subtext).filter(visible=True)
				subtext_targets = text_subtargets.or_(placeholder_subtargets).or_(label_subtargets)
				if subtext_targets.count() > 0:
					targets = targets.or_(subtext_targets)

		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() < self.ith:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Not enough targets found: ' + str(targets.all()))
		else:
			try:
				targets.nth(self.ith).click()
			except TimeoutError:
				return ActionResult(status=ActionResultStatus.FAILURE, message='Click timed out, element might not be clickable')
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the ith element that contains the given text.')


@default_action
class ScrollUp(BaseAction):
	"""Scrolls up on the page."""

	def execute(self, context: ActionContext) -> ActionResult:
		context.page.mouse.wheel(0, -700)
		return ActionResult(status=ActionResultStatus.UNKNOWN, message='Sent scroll up command.')


@default_action
class ScrollDown(BaseAction):
	"""Scrolls down on the page."""

	def execute(self, context: ActionContext) -> ActionResult:
		context.page.mouse.wheel(0, 700)
		return ActionResult(status=ActionResultStatus.UNKNOWN, message='Sent scroll down command.')


@default_action
class ScrollToText(BaseAction):
	"""Searches for the given text on the current page and focuses on it. Will respond with all options if multiple candidates are found."""

	text: str = Field(description='The text to search for.')

	def execute(self, context: ActionContext) -> ActionResult:
		targets = context.page.get_by_text(self.text).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() == 1:
			targets.focus()
			return ActionResult(
				status=ActionResultStatus.SUCCESS, message='Searched for the given text on the current page and focused on it.'
			)
		else:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple targets found: ' + str(targets.all()))


@default_action
class ScrollToIthText(BaseAction):
	"""Searches for the ith given text on the current page and focuses on it."""

	text: str = Field(description='The text to search for.')
	ith: int = Field(description='The index of the element to focus on.')

	def execute(self, context: ActionContext) -> ActionResult:
		targets = context.page.get_by_text(self.text).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() < self.ith:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Not enough targets found: ' + str(targets.all()))
		else:
			targets.nth(self.ith).focus()
			return ActionResult(
				status=ActionResultStatus.SUCCESS, message='Searched for the ith given text on the current page and focused on it.'
			)


@default_action
class TypeText(BaseAction):
	"""Type text into the focused element. You can see your currently focused element in the metadata. Use a click action to focus on a text field, if it is not yet focused.

	IMPORTANT USAGE NOTE:
	For the TypeText action, 'press_enter' MUST be a boolean (True/False), not a string!
	Example: TypeText(text="search term", press_enter=True)
	INCORRECT: TypeText(text="search term", press_enter="press_enter")
	"""

	text: str = Field(description='The text to type into the focused element.')
	press_enter: bool = Field(
		default=False,
		description='TRUE or FALSE only. Set to TRUE to press Enter after typing, FALSE otherwise. Do NOT use strings like "press_enter"!',
	)

	@classmethod
	def page_filter(cls, page: Page) -> bool:
		return page.evaluate('document.activeElement.tagName !== "BODY"')

	def execute(self, context: ActionContext) -> ActionResult:
		try:
			context.page.keyboard.type(self.text)
			if self.press_enter:
				context.page.keyboard.press('Enter')
			return ActionResult(status=ActionResultStatus.SUCCESS, message=f"Typed '{self.text}' into the focused element.")
		except Exception as e:
			return ActionResult(
				status=ActionResultStatus.FAILURE,
				message=f'Could not type into the focused element: {e}',
			)


@default_action
class ClearInputField(BaseAction):
	"""Clears the input field that is currently focused."""

	@classmethod
	def page_filter(cls, page: Page) -> bool:
		return page.evaluate('document.activeElement.hasAttribute("value") && document.activeElement.value != ""')

	def execute(self, context: ActionContext) -> ActionResult:
		try:
			# Clear the input field by setting its value to an empty string
			context.page.evaluate('document.activeElement.value = ""')
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Cleared the input field.')
		except Exception as e:
			return ActionResult(status=ActionResultStatus.FAILURE, message=f'Could not clear the input field: {e}')


# @default_action
# class Fill(BaseAction):
# 	"""Click on the first element that contains the given text and type the given content into it."""

# 	text: str = Field(description='The text of the element to click on.')
# 	content: str = Field(description='The content to fill into the selected field.')

# 	def execute(self, context: ActionContext) -> ActionResult:
# 		targets = context.page.get_by_text(self.text).filter(visible=True)
# 		if targets.count() == 0:
# 			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
# 		else:
# 			targets.first.click()
# 			context.page.keyboard.type(self.content)
# 			message = f'Clicked on the first element that contains {self.text} and filled the given content into it.'
# 			if targets.count() > 1:
# 				message += ' WARNING: Multiple targets found, selected first.'
# 			return ActionResult(
# 				status=ActionResultStatus.SUCCESS,
# 				message=message,
# 			)


@default_action
class ClickByCoords(BaseAction):
	"""Clicks on the given coordinates. Rather unreliable, so should be used as a last resort."""

	x: int = Field(description='The x coordinate to click on.')
	y: int = Field(description='The y coordinate to click on.')

	def execute(self, context: ActionContext) -> ActionResult:
		context.page.mouse.click(self.x, self.y)
		return ActionResult(status=ActionResultStatus.UNKNOWN, message='Clicked on the given coordinates.')


@default_action
class Back(BaseAction):
	"""Go back to the previous page."""

	def execute(self, context: ActionContext) -> ActionResult:
		context.page.go_back()
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Go back to the previous page.')


@default_action
class Reset(BaseAction):
	"""Reset the browser to the initial starting page."""

	def execute(self, context: ActionContext) -> ActionResult:
		try:
			context.page.goto(context.task.url)
			context.page.wait_for_load_state('networkidle')
		except TimeoutError:
			return ActionResult(status=ActionResultStatus.INFO, message='Page did not indicate that it was loaded. Proceeding anyway.')

		return ActionResult(status=ActionResultStatus.SUCCESS, message='Reset the browser to the initial starting page.')


@default_action
class Abort(BaseAction):
	"""Abort the task only in case when you have failed to complete the task and there is no way to recover."""

	reason: str = Field(description='The reason for aborting the task.')

	def execute(self, context: ActionContext) -> ActionResult:
		return ActionResult(status=ActionResultStatus.ABORT, message=f'Task aborted. Reason: {self.reason}')


@default_action
class Finish(BaseAction):
	"""Indicate that the task is finished and provide the final answer/result."""

	answer: str = Field(description='The final answer to the user query.')

	def execute(self, context: ActionContext) -> ActionResult:
		return ActionResult(
			status=ActionResultStatus.FINISH,
			message=f'Task finished. The answer is: {self.answer}',
			data={'answer': self.answer},
		)

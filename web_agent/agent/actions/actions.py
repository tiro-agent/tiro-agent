from playwright.sync_api import Page
from pydantic import Field

from web_agent.agent.actions.base import ActionResult, ActionResultStatus, BaseAction, default_action
from web_agent.agent.schemas import Task


@default_action
class Click(BaseAction):
	"""Clicks a specific element on the page."""

	selector: str = Field(description='The selector to click on.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		targets = page.get_by_text(self.selector).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() == 1:
			targets.click()
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the first element that contains the given text.')
		else:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple targets found: ' + str(targets.all()))


@default_action
class ClickByText(BaseAction):
	"""Clicks on the first element that contains the given text."""

	text: str = Field(description='The text to click on.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		targets = page.get_by_text(self.text).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() == 1:
			targets.click()
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the first element that contains the given text.')
		else:
			targets_str = str([f'{i} -  {str(target.element_handle()).replace("JSHandle@", "")}' for i, target in enumerate(targets.all())])
			return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple targets found: ' + targets_str)


@default_action
class ClickByTextIth(BaseAction):
	"""Clicks on the ith element that contains the given text."""

	text: str = Field(description='The text to click on.')
	ith: int = Field(description='The index of the element to click on.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		targets = page.get_by_text(self.text).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() < self.ith:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Not enough targets found: ' + str(targets.all()))
		else:
			targets.nth(self.ith).click()
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the ith element that contains the given text.')


@default_action
class ScrollUp(BaseAction):
	"""Scrolls up on the page."""

	def execute(self, page: Page, task: Task) -> ActionResult:
		page.mouse.wheel(0, -700)
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Scrolled up on the page.')


@default_action
class ScrollDown(BaseAction):
	"""Scrolls down on the page."""

	def execute(self, page: Page, task: Task) -> ActionResult:
		page.mouse.wheel(0, 700)
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Scrolled down on the page.')


@default_action
class SearchText(BaseAction):
	"""Searches for the given text on the current page and focuses on it."""

	text: str = Field(description='The text to search for.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		targets = page.get_by_text(self.text).filter(visible=True)
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
class TypeText(BaseAction):
	"""Type text into the focused element."""

	text: str = Field(description='The text to type into the focused element.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		try:
			page.keyboard.type(self.text)
			return ActionResult(status=ActionResultStatus.SUCCESS, message=f"Typed '{self.text}' into the focused element.")
		except Exception as e:
			return ActionResult(
				status=ActionResultStatus.FAILURE,
				message=f'Could not type into the focused element: {e}',
			)


@default_action
class Fill(BaseAction):
	"""Click on the first element that contains the given text and type the given content into it."""

	text: str = Field(description='The text of the element to click on.')
	content: str = Field(description='The content to fill into the selected field.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		targets = page.get_by_text(self.text).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		else:
			targets.first.click()
			page.keyboard.type(self.content)
			message = f'Clicked on the first element that contains {self.text} and filled the given content into it.'
			if targets.count() > 1:
				message += ' WARNING: Multiple targets found, selected first.'
			return ActionResult(
				status=ActionResultStatus.SUCCESS,
				message=message,
			)


@default_action
class ClickCoord(BaseAction):
	"""Clicks on the given coordinates."""

	x: int = Field(description='The x coordinate to click on.')
	y: int = Field(description='The y coordinate to click on.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		page.mouse.click(self.x, self.y)
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the given coordinates.')


@default_action
class Back(BaseAction):
	"""Go back to the previous page."""

	def execute(self, page: Page, task: Task) -> ActionResult:
		page.evaluate('window.history.back()')
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Go back to the previous page.')


@default_action
class Reset(BaseAction):
	"""Reset the browser to the initial starting page."""

	def execute(self, page: Page, task: Task) -> ActionResult:
		try:
			page.goto(task.url)
			page.wait_for_load_state('networkidle')
		except TimeoutError:
			return ActionResult(status=ActionResultStatus.INFO, message='Page did not indicate that it was loaded. Proceeding anyway.')

		return ActionResult(status=ActionResultStatus.SUCCESS, message='Reset the browser to the initial starting page.')


@default_action
class Abort(BaseAction):
	"""Abort the task only in case when you have failed to complete the task and there is no way to recover."""

	reason: str = Field(description='The reason for aborting the task.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		return ActionResult(status=ActionResultStatus.ABORT, message=f'Task aborted. Reason: {self.reason}')


@default_action
class Finish(BaseAction):
	"""Indicate that the task is finished and provide the final answer/result."""

	answer: str = Field(description='The final answer to the user query.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		return ActionResult(
			status=ActionResultStatus.FINISH,
			message=f'Task finished. The answer is: {self.answer}',
			data={'answer': self.answer},
		)

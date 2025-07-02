import asyncio

from playwright._impl._errors import TimeoutError
from playwright.async_api import Page
from pydantic import Field

from web_agent.agent.actions.base import (
	ActionContext,
	ActionResult,
	ActionResultStatus,
	BaseAction,
	ContextChange,
	ContextChangeTypes,
	default_action,
)
from web_agent.browser.browser import pretty_print_element


@default_action
class ClickByText(BaseAction):
	"""Clicks the element that contains the given text. Will respond with all options if multiple candidates are found. If no elements are found, it tries looking for subtexts."""  # noqa: E501

	text: str = Field(description='The text to click on.')

	async def execute(self, context: ActionContext) -> ActionResult:
		text_targets = context.page.get_by_text(self.text).filter(visible=True)
		placeholder_targets = context.page.get_by_placeholder(self.text).filter(visible=True)
		label_targets = context.page.get_by_label(self.text).filter(visible=True)
		targets = text_targets.or_(placeholder_targets).or_(label_targets)

		if await targets.count() == 0:  # If no targets found, try to find subtexts
			for subtext in self.text.split():
				text_subtargets = context.page.get_by_text(subtext).filter(visible=True)
				placeholder_subtargets = context.page.get_by_placeholder(subtext).filter(visible=True)
				label_subtargets = context.page.get_by_label(subtext).filter(visible=True)
				subtext_targets = text_subtargets.or_(placeholder_subtargets).or_(label_subtargets)
				if await subtext_targets.count() > 0:
					targets = targets.or_(subtext_targets)

		if await targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif await targets.count() == 1:
			try:
				await targets.click()
			except TimeoutError:
				return ActionResult(status=ActionResultStatus.FAILURE, message='Click timed out, element might not be clickable')
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the element that contains the given text.')
		else:
			all_targets = await targets.all()
			pretty_targets = []
			for i, target in enumerate(all_targets):
				element_handle = await target.element_handle()
				if element_handle:
					pretty_targets.append(f'{i} -  {await pretty_print_element(element_handle)}')

			targets_str = str(pretty_targets)
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

	async def execute(self, context: ActionContext) -> ActionResult:
		text_targets = context.page.get_by_text(self.text).filter(visible=True)
		placeholder_targets = context.page.get_by_placeholder(self.text).filter(visible=True)
		label_targets = context.page.get_by_label(self.text).filter(visible=True)
		targets = text_targets.or_(placeholder_targets).or_(label_targets)

		if await targets.count() == 0:  # If no targets found, try to find subtexts
			for subtext in self.text.split():
				text_subtargets = context.page.get_by_text(subtext).filter(visible=True)
				placeholder_subtargets = context.page.get_by_placeholder(subtext).filter(visible=True)
				label_subtargets = context.page.get_by_label(subtext).filter(visible=True)
				subtext_targets = text_subtargets.or_(placeholder_subtargets).or_(label_subtargets)
				if await subtext_targets.count() > 0:
					targets = targets.or_(subtext_targets)

		if await targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif await targets.count() < self.ith:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Not enough targets found: ' + str(await targets.all()))
		else:
			try:
				await targets.nth(self.ith).click()
			except TimeoutError:
				return ActionResult(status=ActionResultStatus.FAILURE, message='Click timed out, element might not be clickable')
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the ith element that contains the given text.')


@default_action
class ScrollUp(BaseAction):
	"""Scrolls up on the page."""

	async def execute(self, context: ActionContext) -> ActionResult:
		before_scroll_y = await context.page.evaluate('window.scrollY')
		print(f'Page Y before scrolling: {before_scroll_y}')
		await context.page.mouse.wheel(0, -700)
		await asyncio.sleep(1)
		after_scroll_y = await context.page.evaluate('window.scrollY')
		print(f'Page Y after scrolling: {after_scroll_y}')

		if before_scroll_y == after_scroll_y:
			return ActionResult(
				status=ActionResultStatus.FAILURE, message='No scrolling detected, you might already be at the top of the page.'
			)
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Scrolled up.')


@default_action
class ScrollDown(BaseAction):
	"""Scrolls down on the page."""

	async def execute(self, context: ActionContext) -> ActionResult:
		before_scroll_y = await context.page.evaluate('window.scrollY')
		print(f'Page Y before scrolling: {before_scroll_y}')
		await context.page.mouse.wheel(0, 700)
		await asyncio.sleep(1)
		after_scroll_y = await context.page.evaluate('window.scrollY')
		print(f'Page Y after scrolling: {after_scroll_y}')

		if before_scroll_y == after_scroll_y:
			return ActionResult(
				status=ActionResultStatus.FAILURE, message='No scrolling detected, you might already be at the bottom of the page.'
			)
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Scrolled down.')


@default_action
class ScrollToText(BaseAction):
	"""Searches for the given text on the current page and focuses on it. Will respond with all options if multiple candidates are found."""

	text: str = Field(description='The text to search for.')

	async def execute(self, context: ActionContext) -> ActionResult:
		targets = context.page.get_by_text(self.text).filter(visible=True)
		if await targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif await targets.count() == 1:
			try:
				await targets.focus()
				return ActionResult(
					status=ActionResultStatus.SUCCESS, message='Searched for the given text on the current page and focused on it.'
				)
			except TimeoutError:
				return ActionResult(status=ActionResultStatus.FAILURE, message='Focus timed out, element might not be focusable')
		else:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple targets found: ' + str(await targets.all()))


@default_action
class ScrollToIthText(BaseAction):
	"""Searches for the ith given text on the current page and focuses on it."""

	text: str = Field(description='The text to search for.')
	ith: int = Field(description='The index of the element to focus on.')

	async def execute(self, context: ActionContext) -> ActionResult:
		targets = context.page.get_by_text(self.text).filter(visible=True)
		if await targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif await targets.count() < self.ith:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Not enough targets found: ' + str(await targets.all()))
		else:
			try:
				await targets.nth(self.ith).focus()
				return ActionResult(
					status=ActionResultStatus.SUCCESS, message='Searched for the ith given text on the current page and focused on it.'
				)
			except TimeoutError:
				return ActionResult(status=ActionResultStatus.FAILURE, message='Focus timed out, element might not be focusable')


@default_action
class TypeText(BaseAction):
	"""Type text into the focused element. You can see your currently focused element in the metadata. Use a click action to focus on a text field, if it is not yet focused.

	IMPORTANT USAGE NOTE:
	For the TypeText action, 'press_enter' MUST be a boolean (True/False), not a string!
	Example: TypeText(text="search term", press_enter=True)
	INCORRECT: TypeText(text="search term", press_enter="press_enter")
	"""  # noqa: E501

	text: str = Field(description='The text to type into the focused element.')
	press_enter: bool = Field(
		default=False,
		description='TRUE or FALSE only. Set to TRUE to press Enter after typing, FALSE otherwise. Do NOT use strings like "press_enter"!',
	)

	@classmethod
	async def page_filter(cls, page: Page) -> bool:
		return await page.evaluate('document.activeElement.tagName !== "BODY"')

	async def execute(self, context: ActionContext) -> ActionResult:
		try:
			await context.page.keyboard.type(self.text)
			if self.press_enter:
				await context.page.keyboard.press('Enter')
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
	async def page_filter(cls, page: Page) -> bool:
		return await page.evaluate('document.activeElement.hasAttribute("value") && document.activeElement.value != ""')

	async def execute(self, context: ActionContext) -> ActionResult:
		try:
			# Clear the input field by setting its value to an empty string
			await context.page.evaluate('document.activeElement.value = ""')
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Cleared the input field.')
		except Exception as e:
			return ActionResult(status=ActionResultStatus.FAILURE, message=f'Could not clear the input field: {e}')


@default_action
class ClickByCoords(BaseAction):
	"""Clicks on the given coordinates. Rather unreliable, so should be used as a last resort."""

	x: int = Field(description='The x coordinate to click on.')
	y: int = Field(description='The y coordinate to click on.')

	async def execute(self, context: ActionContext) -> ActionResult:
		# evaluate the mouse-helper.js file to show the mouse pointer in the screenshots

		pre_action_screenshot = await context.page.screenshot()

		with open('web_agent/agent/actions/mouse-helper.js') as f:
			js_code = f.read()

		await context.page.evaluate(js_code)
		await context.page.evaluate("window['mouse-helper']();")
		await context.page.wait_for_timeout(300)
		await context.page.mouse.move(self.x, self.y)
		await context.page.wait_for_timeout(300)
		screenshot = await context.page.screenshot()

		await context.page.mouse.click(self.x, self.y, delay=150)

		await context.page.evaluate("window['mouse-helper-destroy']();")

		post_action_screenshot = await context.page.screenshot()

		if pre_action_screenshot == post_action_screenshot:
			return ActionResult(
				status=ActionResultStatus.FAILURE,
				message='Clicked on the given coordinates. The mouse pointer is visible in the screenshot.'
				+ ' But it does not appear to have changed anything on the page.'
				+ ' If the desired outcome was not achieved, try to slightly adjust the coordinates, and try again.',
				context_change=ContextChange(action=ContextChangeTypes.SCREENSHOT, data={'screenshot': screenshot}),
			)
		else:
			return ActionResult(
				status=ActionResultStatus.UNKNOWN,
				message='Clicked on the given coordinates. The mouse pointer is visible in the screenshot.'
				+ ' If the desired outcome was not achieved, try to slightly adjust the coordinates, and try again.',
				context_change=ContextChange(action=ContextChangeTypes.SCREENSHOT, data={'screenshot': screenshot}),
			)


@default_action
class Back(BaseAction):
	"""Go back to the previous page."""

	async def execute(self, context: ActionContext) -> ActionResult:
		await context.page.go_back()
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Go back to the previous page.')


@default_action
class Reset(BaseAction):
	"""Reset the browser to the initial starting page."""

	async def execute(self, context: ActionContext) -> ActionResult:
		try:
			await context.page.goto(context.task.url)
			await context.page.wait_for_load_state('networkidle')
		except TimeoutError:
			return ActionResult(status=ActionResultStatus.INFO, message='Page did not indicate that it was loaded. Proceeding anyway.')

		return ActionResult(status=ActionResultStatus.SUCCESS, message='Reset the browser to the initial starting page.')


@default_action
class Abort(BaseAction):
	"""Abort the task only in case when you have failed to complete the task and there is no way to recover."""

	reason: str = Field(description='The reason for aborting the task.')

	async def execute(self, context: ActionContext) -> ActionResult:
		return ActionResult(status=ActionResultStatus.ABORT, message=f'Task aborted. Reason: {self.reason}')


@default_action
class Finish(BaseAction):
	"""Indicate that the task is finished and provide the final answer/result."""

	answer: str = Field(description='The final answer to the user query.')

	async def execute(self, context: ActionContext) -> ActionResult:
		return ActionResult(
			status=ActionResultStatus.FINISH,
			message=f'Task finished. The answer is: {self.answer}',
			data={'answer': self.answer},
		)

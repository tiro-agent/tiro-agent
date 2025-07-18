import asyncio
from typing import ClassVar

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

	# This is a hack to limit the number of targets to avoid overwhelming the LLM
	MAX_TARGETS: ClassVar[int] = 50

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
			all_targets = (await targets.all())[: self.MAX_TARGETS]
			target_descriptions = []
			for i, target in enumerate(all_targets):
				try:
					element_handle = await target.element_handle()
					description = await pretty_print_element(element_handle)
					target_descriptions.append(f'{i} -  {description}')
				except Exception:
					target_descriptions.append(f'{i} -  <element unavailable>')
			targets_str = str(target_descriptions)
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
		try:
			before_scroll_y = await context.page.evaluate('window.scrollY')
		except Exception:
			# Handle cases where execution context is destroyed, assume starting from 0
			before_scroll_y = 0

		print(f'Page Y before scrolling: {before_scroll_y}')
		await context.page.mouse.wheel(0, -700)
		await asyncio.sleep(1)

		try:
			after_scroll_y = await context.page.evaluate('window.scrollY')
		except Exception:
			# Handle cases where execution context is destroyed, assume scroll succeeded
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Scrolled up.')

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
		try:
			before_scroll_y = await context.page.evaluate('window.scrollY')
		except Exception:
			# Handle cases where execution context is destroyed, assume starting from 0
			before_scroll_y = 0

		print(f'Page Y before scrolling: {before_scroll_y}')
		await context.page.mouse.wheel(0, 700)
		await asyncio.sleep(1)

		try:
			after_scroll_y = await context.page.evaluate('window.scrollY')
		except Exception:
			# Handle cases where execution context is destroyed, assume scroll succeeded
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Scrolled down.')

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
		try:
			return await page.evaluate('document.activeElement.tagName !== "BODY"')
		except Exception:
			# Handle cases where execution context is destroyed (e.g., due to navigation)
			return False

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
		try:
			return await page.evaluate('document.activeElement.hasAttribute("value") && document.activeElement.value != ""')
		except Exception:
			# Handle cases where execution context is destroyed (e.g., due to navigation)
			return False

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

	async def _get_dom_state(self, page: Page) -> dict:
		"""Captures a snapshot of key UI elements on the page."""
		try:
			return await page.evaluate("""
				() => {
					const state = { alerts: [], modals: [], validationMessages: [] };
					const an_sel = '[role="alert"], .alert, .notification';
					const m_sel = '[role="dialog"], .modal, .popup';
					const v_sel = '.error, .success, [role="status"]';

					document.querySelectorAll(an_sel).forEach(el => {
						if (el.offsetParent !== null) state.alerts.push({ text: el.textContent.trim(), classes: el.className });
					});
					document.querySelectorAll(m_sel).forEach(el => {
						if (el.style.display !== 'none' && el.offsetParent !== null) state.modals.push({ text: el.textContent.trim(), classes: el.className });
					});
					document.querySelectorAll(v_sel).forEach(el => {
						if (el.offsetParent !== null && el.textContent.trim()) state.validationMessages.push({ text: el.textContent.trim(), classes: el.className });
					});
					return state;
				}
			""")
		except Exception:
			# Handle cases where execution context is destroyed (e.g., due to navigation)
			return {'alerts': [], 'modals': [], 'validationMessages': []}

	async def _wait_for_change(self, context: ActionContext, action_coro: callable) -> tuple[bool, str]:
		"""
		Performs an action and waits for various types of page changes to occur.
		Returns a tuple of (change_detected, change_type).
		"""
		import asyncio

		from playwright._impl._errors import TargetClosedError

		initial_url = context.page.url
		initial_state = await self._get_dom_state(context.page)

		# Set up event listeners BEFORE the action
		tasks = []
		try:
			tasks = [
				asyncio.create_task(context.page.wait_for_event('framenavigated'), name='navigation'),
				asyncio.create_task(context.page.wait_for_event('request'), name='network_activity'),
				asyncio.create_task(context.page.wait_for_event('dialog'), name='dialog_opened'),
			]
		except TargetClosedError:
			# If the page is already closed, we can't wait for events
			return False, 'target_closed'

		try:
			await action_coro()
		except TargetClosedError:
			# Handle case where browser is closed during action execution
			for task in tasks:
				task.cancel()
			if tasks:
				await asyncio.gather(*tasks, return_exceptions=True)
			return False, 'target_closed'

		# Race for the first event to complete with a 2-second timeout
		try:
			done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=2.0)
		except TargetClosedError:
			# Handle case where browser is closed during wait
			for task in tasks:
				task.cancel()
			if tasks:
				await asyncio.gather(*tasks, return_exceptions=True)
			return False, 'target_closed'

		# Clean up tasks that didn't complete
		for task in pending:
			task.cancel()

		# Wait for cancelled tasks to finish and retrieve their exceptions to avoid warnings
		if pending:
			try:
				await asyncio.gather(*pending, return_exceptions=True)
			except TargetClosedError:
				pass  # Ignore TargetClosedError during cleanup

		if done:
			for task in done:
				try:
					task.result()  # Raise exception if task failed
					return True, task.get_name()
				except (Exception, TargetClosedError):
					continue  # Ignore failed/cancelled tasks

		# Fallback checks if no events fired quickly
		try:
			if context.page.url != initial_url:
				return True, 'url_change'

			await context.page.wait_for_timeout(300)  # Give DOM a moment to settle
			new_state = await self._get_dom_state(context.page)
		except TargetClosedError:
			# Page was closed during fallback checks
			return False, 'target_closed'

		def states_different(old: dict, new: dict) -> bool:
			for key in ['alerts', 'modals', 'validationMessages']:
				if len(old[key]) != len(new[key]):
					return True
				old_items = {f'{item["text"]}_{item["classes"]}' for item in old[key]}
				new_items = {f'{item["text"]}_{item["classes"]}' for item in new[key]}
				if old_items != new_items:
					return True
			return False

		if states_different(initial_state, new_state):
			return True, 'dom_change'

		return False, 'unknown'

	async def execute(self, context: ActionContext) -> ActionResult:
		# Determine device pixel ratio and adjust coordinates
		try:
			pixel_ratio = await context.page.evaluate('() => window.devicePixelRatio')
		except Exception:
			# Handle cases where execution context is destroyed, fallback to default ratio
			pixel_ratio = 1.0

		x_coord = self.x / pixel_ratio
		y_coord = self.y / pixel_ratio

		if not context.mouse_cursor:
			# Show mouse helper for visual feedback
			try:
				with open('web_agent/agent/actions/mouse-helper.js') as f:
					js_code = f.read()

				await context.page.evaluate(js_code)
				await context.page.evaluate("window['mouse-helper']();")
				await context.page.wait_for_timeout(300)
			except Exception:
				# Handle cases where execution context is destroyed, continue without mouse helper
				pass

		await context.page.mouse.move(x_coord, y_coord)
		await context.page.wait_for_timeout(300)
		screenshot = await context.page.screenshot()

		async def click_action() -> None:
			await context.page.mouse.click(x_coord, y_coord, delay=150)

		change_detected, change_type = await self._wait_for_change(context, click_action)

		if not context.mouse_cursor:
			try:
				await context.page.evaluate("window['mouse-helper-destroy']();")
			except Exception:
				# Handle cases where execution context is destroyed, continue without cleanup
				pass

		if change_detected:
			return ActionResult(
				status=ActionResultStatus.SUCCESS,
				message=f'Clicked on coordinates ({self.x}, {self.y}). Change detected: {change_type}. The mouse pointer is visible in the screenshot.',  # noqa: E501
				context_change=ContextChange(action=ContextChangeTypes.SCREENSHOT, data={'screenshot': screenshot}),
			)
		else:
			return ActionResult(
				status=ActionResultStatus.UNKNOWN,
				message=f'Clicked on coordinates ({self.x}, {self.y}). No obvious changes detected. Adjust the coordinates, and try again. Do not try again with the same coordinates. Try adding/removing a few pixels up or down, left or right. Analyze the position of the cursor in the screenshot, that is the position the click was made.',  # noqa: E501
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

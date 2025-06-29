import types

from playwright._impl._errors import Error, TimeoutError
from playwright._impl._js_handle import JSHandle
from playwright.async_api import Playwright, async_playwright


async def get_js_attr(node: JSHandle, attr: str) -> str:
	return await node.evaluate(f'node => node.{attr}')


async def pretty_print_element(node: JSHandle) -> str:
	html_tag = (await get_js_attr(node, 'tagName')).lower()
	html_id = await get_js_attr(node, 'id')
	html_text = (await get_js_attr(node, 'innerText'))[:50]

	if html_tag == 'a':
		html_href = await get_js_attr(node, 'href')
		return f'<a href="{html_href}" id="{html_id}">{html_text}</a>'
	elif html_tag == 'input':
		html_type = await get_js_attr(node, 'type')
		html_name = await get_js_attr(node, 'name')
		html_placeholder = await get_js_attr(node, 'placeholder')
		return f'<input type="{html_type}" id="{html_id}" name="{html_name}" placeholder="{html_placeholder}" value="{html_text}">'
	elif html_tag == 'body':
		return None  # Body tag is not useful to print
	else:
		return f'<{html_tag} id="{html_id}">{html_text}</{html_tag}>'


class Browser:
	def __init__(self) -> None:
		self.playwright: Playwright | None = None
		self.browser = None
		self.page = None

	async def __aenter__(self) -> 'Browser':
		self.playwright = await async_playwright().start()
		browser = await self.playwright.chromium.launch(
			headless=False,
			channel='chrome',
		)
		self.browser = await browser.new_context(viewport={'width': 1920, 'height': 1080})
		self.page = await self.browser.new_page()
		return self

	async def load_url(self, url: str) -> None:
		try:
			await self.page.goto(url)
			await self.page.wait_for_load_state('networkidle')
		except TimeoutError:
			print('TimeoutError: Page did not indicate that it was loaded. Proceeding anyway.')
		except Error:
			print("Page couldn't load, moving on to next task.")
			raise Exception('Could not load the URL') from Error

	async def clean_page(self) -> None:
		try:
			await self.page.locator('a').evaluate_all('nodes => nodes.forEach(node => node.removeAttribute("target"))')
		except Error:
			print('WARNING: page cleanup failed, proceeding anyways and hoping for automatic recovery in next step')

	async def get_html(self) -> str:
		return await self.page.content()

	async def get_metadata(self) -> dict[str, str]:
		return {
			'title': await self.page.title(),
			'url': self.page.url,
			# 'description': self.page.meta.get('description', ''),
			# 'is_scrollable': await self.page.evaluate('document.body.scrollHeight > document.body.clientHeight')
			# TODO: add more useful metadata
			'focused_element': await pretty_print_element(await self.page.evaluate_handle('document.activeElement')),
		}

	async def save_screenshot(self, screenshot_path: str) -> bytes:
		"""Saves the screenshot to the given path and returns the bytes of the screenshot."""
		await self.page.screenshot(path=screenshot_path)  # TODO: check full page screenshots
		return open(screenshot_path, 'rb').read()

	async def click_by_text(self, text: str, i: int | None = None) -> tuple[bool, str]:
		targets = self.page.get_by_text(text).filter(visible=True)

		if i and await targets.count() <= i:
			return False, 'Index out of bounds'

		if await targets.count() == 0:
			return False, 'Text not found on page'
		elif await targets.count() == 1:
			await targets.click()
			return True, ''
		elif i is not None:
			await targets.nth(i).click()
			return True, ''
		else:
			all_targets = await targets.all()
			targets_str = str(
				[f'{i} -  {str(await target.element_handle()).replace("JSHandle@", "")}' for i, target in enumerate(all_targets)]
			)
			return False, f'Multiple targets found: {targets_str}'

	async def search_and_highlight(self, text: str) -> tuple[bool, str]:
		targets = self.page.get_by_text(text).filter(visible=True)
		if await targets.count() == 0:
			return False, 'Text not found on page'
		elif await targets.count() == 1:
			await targets.focus()
			return True, ''
		else:
			return False, 'Multiple targets found: ' + str(await targets.all())

	async def fill_closest_input_to_text(self, text: str, value: str) -> None:
		locator = self.page.get_by_text(text).filter(visible=True)

		for elem in await locator.all():
			print(await elem.text_content())

		await locator.first.fill(value)

	async def __aexit__(
		self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None
	) -> None:
		await self.playwright.stop()

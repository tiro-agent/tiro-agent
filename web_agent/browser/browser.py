import types

from playwright._impl._errors import Error, TimeoutError
from playwright._impl._js_handle import JSHandle
from playwright.async_api import Playwright, async_playwright


async def get_js_attr(node: JSHandle, attr: str) -> str:
	"""
	Returns the value of a given attribute of a JSHandle.

	:param node: The JSHandle of the element.
	:param attr: The attribute to get the value of.
	:return: The value of the attribute.
	"""
	return await node.evaluate(f'node => node.{attr}')


async def pretty_print_element(node: JSHandle) -> str | None:
	"""
	Returns a pretty-printed HTML representation of a given JSHandle, which is easier to read for humans and LLMs.

	:param node: The JSHandle of the element to pretty-print.
	:return: A string containing the pretty-printed HTML.
	"""
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
		return None  # Body tag is not useful to print as it indicates the entire webpage.
	else:
		return f'<{html_tag} id="{html_id}">{html_text}</{html_tag}>'


class Browser:
	"""
	This class provides a browser instance using Playwright. It supports loading, screenshotting and interacting with a
	web page.
	"""

	def __init__(self) -> None:
		self.playwright: Playwright | None = None
		self.browser = None
		self.page = None

	async def __aenter__(self) -> 'Browser':
		"""
		Starts the Playwright instance and opens a new browser context.

		:return: The Browser instance.
		"""
		self.playwright = await async_playwright().start()
		browser = await self.playwright.chromium.launch(
			headless=False,
			channel='chrome',
		)
		self.browser = await browser.new_context(viewport={'width': 1920, 'height': 1080})
		self.page = await self.browser.new_page()
		return self

	async def load_url(self, url: str) -> None:
		"""
		Loads the given URL in the browser and handles various response errors.

		:param url: The URL to load.
		"""
		try:
			response = await self.page.goto(url)
			await self.page.wait_for_load_state('networkidle')

			if response.status in [400, 401, 403, 404, 408, 429, 500, 502, 503, 504]:
				print(f'Page returned status code {response.status}')
				raise Exception(f'Page returned status code {response.status}')
		except TimeoutError:
			print('TimeoutError: Page did not indicate that it was loaded. Proceeding anyway.')
			if response.status in [400, 401, 403, 404, 408, 429, 500, 502, 503, 504]:
				print(f'Page returned status code {response.status}')
				raise Exception(f'Page returned status code {response.status}') from TimeoutError
		except Exception as e:
			print("Page couldn't load, moving on to next task.")
			raise Exception('Could not load the URL') from e

	async def clean_page(self) -> None:
		"""
		Cleans the page's HTML code.
		"""
		try:
			# Remove target attributes from all a tags to prevent links opening in a new window.
			await self.page.locator('a').evaluate_all('nodes => nodes.forEach(node => node.removeAttribute("target"))')
		except Error:
			print('WARNING: page cleanup failed, proceeding anyways and hoping for automatic recovery in next step')

	async def get_html(self) -> str:
		"""
		Returns the HTML code of the current page.

		:return: The HTML code of the current page.
		"""
		return await self.page.content()

	async def get_metadata(self) -> dict[str, str]:
		"""
		Returns some metadata of the current page.

		:return: A dictionary containing the page's title, URL, and focused element.
		"""
		try:
			focused_element = await pretty_print_element(await self.page.evaluate_handle('document.activeElement'))
		except Exception:
			# Handle cases where execution context is destroyed (e.g., due to navigation)
			focused_element = 'Unable to determine focused element.'

		return {
			'title': await self.page.title(),
			'url': self.page.url,
			# 'description': self.page.meta.get('description', ''),
			# 'is_scrollable': await self.page.evaluate('document.body.scrollHeight > document.body.clientHeight')
			# TODO: add more useful metadata
			'focused_element': focused_element,
		}

	async def save_screenshot(self, screenshot_path: str) -> bytes:
		"""
		Saves the screenshot of the current page to the given path and returns the bytes of the screenshot.

		:param screenshot_path: The path to save the screenshot to.
		:return: The bytes of the screenshot.
		"""
		await self.page.screenshot(path=screenshot_path)  # TODO: check full page screenshots
		return open(screenshot_path, 'rb').read()

	async def __aexit__(
		self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None
	) -> None:
		"""
		Stops the Playwright instance and closes the browser context.
		"""
		await self.playwright.stop()

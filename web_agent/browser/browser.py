import types

from playwright._impl._errors import TimeoutError, Error
from playwright.sync_api import sync_playwright
from playwright._impl._js_handle import JSHandle


def get_js_attr(node: JSHandle, attr: str) -> str:
	return node.evaluate(f'node => node.{attr}')

def pretty_print_element(node: JSHandle) -> str:
	html_tag = get_js_attr(node, 'tagName').lower()
	html_id = get_js_attr(node, 'id')
	html_text = get_js_attr(node, 'innerText')

	if html_tag == 'a':
		html_href = get_js_attr(node, 'href')
		return f'<a href="{html_href}" id="{html_id}">{html_text}</a>'
	else:
		return f'<{html_tag} id="{html_id}">{html_text}</{html_tag}>'


class Browser:
	def __init__(self, headless: bool = False, browser: str = 'chromium') -> None:
		self.headless = headless
		self.browser_type = browser

	def __enter__(self) -> 'Browser':
		self.playwright = sync_playwright().start()
		self.browser = self.playwright.chromium.launch_persistent_context(
			headless=self.headless,
			channel='chrome',
			user_data_dir='./.browser_user_data',
		)
		self.page = self.browser.new_page()
		# stealth_sync(self.page)   # https://github.com/microsoft/playwright/issues/33529
		return self

	def load_url(self, url: str) -> None:
		try:
			self.page.goto(url)
			self.page.wait_for_load_state('networkidle')
			# time.sleep(10)
		except TimeoutError:
			print('TimeoutError: Page did not indicate that it was loaded. Proceeding anyway.')
		except Error:
			print('Page couldn\'t load, moving on to next task.')
			raise Exception('Could not load the URL')


	def clean_page(self) -> None:
		try:
			self.page.locator('a').evaluate_all('nodes => nodes.forEach(node => node.removeAttribute("target"))')
		except Error:
			print('WARNING: page cleanup failed, proceeding anyways and hoping for automatic recovery in next step')

	def get_html(self) -> str:
		return self.page.content()

	def get_metadata(self) -> dict[str, str]:
		return {
			'title': self.page.title(),
			'url': self.page.url,
			# 'description': self.page.meta.get('description', ''),
			# 'is_scrollable': self.page.evaluate('document.body.scrollHeight > document.body.clientHeight')
			# TODO: add more useful metadata
		}

	def save_screenshot(self, screenshot_path: str) -> bytes:
		"""Saves the screenshot to the given path and returns the bytes of the screenshot."""
		self.page.screenshot(path=screenshot_path)  # TODO: check full page screenshots
		return open(screenshot_path, 'rb').read()

	def click_by_text(self, text: str, i: int | None = None) -> tuple[bool, str]:
		targets = self.page.get_by_text(text).filter(visible=True)

		if i and targets.count() <= i:
			return False, 'Index out of bounds'

		if targets.count() == 0:
			return False, 'Text not found on page'
		elif targets.count() == 1:
			targets.click()
			return True, ''
		elif i is not None:
			targets.nth(i).click()
			return True, ''
		else:
			targets_str = str([f'{i} -  {str(target.element_handle()).replace("JSHandle@", "")}' for i, target in enumerate(targets.all())])
			return False, f'Multiple targets found: {targets_str}'

	def search_and_highlight(self, text: str) -> tuple[bool, str]:
		targets = self.page.get_by_text(text).filter(visible=True)
		if targets.count() == 0:
			return False, 'Text not found on page'
		elif targets.count() == 1:
			targets.focus()
			return True, ''
		else:
			return False, 'Multiple targets found: ' + str(targets.all())

	def fill_closest_input_to_text(self, text: str, value: str) -> None:
		locator = self.page.get_by_text(text).filter(visible=True)

		for elem in locator.all():
			print(elem.text_content())

		locator.first.fill(value)

	def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None:
		self.playwright.stop()

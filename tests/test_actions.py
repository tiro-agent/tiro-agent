from typing import ClassVar

import pytest
from pydantic import Field

from web_agent.agent.actions.base import ActionResult, ActionResultStatus, BaseAction
from web_agent.agent.actions.parser import ActionParser
from web_agent.agent.actions.registry import ActionsRegistry


class Page:
	"""A dummy page class."""

	def __init__(self, url: str) -> None:
		self._url = url

	@property
	async def url(self) -> str:
		return self._url


class DummyClickTextAction(BaseAction):
	"""Clicks on the first element that contains the given text."""

	text: str = Field(description='The text to click on.')

	async def execute(self, page: Page) -> ActionResult:
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message')


class DummyTypeAction(BaseAction):
	"""Types text into the focused element."""

	selector: str = Field(description='The selector to type into.')
	text: str = Field(description='The text to type into the focused element.')

	async def execute(self, page: Page) -> ActionResult:
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message 2')


class DummyClickCoordAction(BaseAction):
	"""Clicks on the given coordinates."""

	x: int = Field(description='The x coordinate to click on.')
	y: int = Field(description='The y coordinate to click on.')

	async def execute(self, page: Page) -> ActionResult:
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message 3')


class TestBaseAction:
	"""Tests the base action class."""

	def test_get_action_name(self) -> None:
		"""Tests if the action name is generated correctly."""
		assert DummyClickTextAction.get_action_name() == 'dummy_click_text_action'
		assert DummyTypeAction.get_action_name() == 'dummy_type_action'
		assert DummyClickCoordAction.get_action_name() == 'dummy_click_coord_action'

		class MyLLMAction(BaseAction):
			async def execute(self, page: Page) -> ActionResult:
				return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message')

		assert MyLLMAction.get_action_name() == 'my_llm_action'

	async def test_is_applicable_domain_filter(self) -> None:
		"""Tests if the domain filter is applied correctly."""

		# test with no domains and no page filter
		class DummyActionNoFilter(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = None

		page = Page(url='https://www.google.com')
		assert await DummyActionNoFilter.is_applicable(page)

		# test with single domain filter (positive)
		class DummyActionGoogle(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['google.com']

		page = Page(url='https://google.com')
		assert await DummyActionGoogle.is_applicable(page)

		page = Page(url='https://www.google.com')
		assert await DummyActionGoogle.is_applicable(page)

		class DummyActionWildcardGoogle(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['*.google.com']

		page = Page(url='https://www.google.com')
		assert await DummyActionWildcardGoogle.is_applicable(page)

		# test with multiple domains filter (positive)
		class DummyActionMultipleDomains(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['test.com', '*.test.com', '*.google.com']

		page = Page(url='https://test.com')
		assert await DummyActionMultipleDomains.is_applicable(page)
		page = Page(url='https://www.test.com')
		assert await DummyActionMultipleDomains.is_applicable(page)
		page = Page(url='https://www.google.com')
		assert await DummyActionMultipleDomains.is_applicable(page)
		page = Page(url='https://www.test.google.com')
		assert await DummyActionMultipleDomains.is_applicable(page)

		# test with domains filter (negative)
		class DummyActionTestDomain(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['*.test.com']

		page = Page(url='https://www.google.com')
		assert not await DummyActionTestDomain.is_applicable(page)

		# test with multiple domains filter (negative)
		class DummyActionMultipleDomainsNegative(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['test.com', '*.test.com', '*.google.com']

		page = Page(url='https://example.com')
		assert not await DummyActionMultipleDomainsNegative.is_applicable(page)

		# test with empty domains filter -> makes it negative for all pages
		class DummyActionEmptyDomains(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = []

		page = Page(url='https://www.google.com')
		assert not await DummyActionEmptyDomains.is_applicable(page)

		# test with * domains filter -> should raise an error, is not allowed (to allow for all set domains to None)
		with pytest.raises(ValueError):

			class DummyActionWildcardDomain(DummyClickTextAction):
				domains: ClassVar[list[str] | None] = ['*']

			page = Page(url='https://www.google.com')
			await DummyActionWildcardDomain.is_applicable(page)

	async def test_is_applicable_page_filter(self) -> None:
		"""Tests if the page filter is applied correctly."""

		# test with page filter (positive)
		class DummyActionPageFilterPositive(DummyClickTextAction):
			@classmethod
			async def page_filter(cls, page: Page) -> bool:
				return await page.url == 'https://google.com'

		page = Page(url='https://google.com')
		assert await DummyActionPageFilterPositive.is_applicable(page)

		# test with page filter (negative)
		class DummyActionPageFilterNegative(DummyClickTextAction):
			@classmethod
			async def page_filter(cls, page: Page) -> bool:
				return await page.url == 'https://google.com'

		page = Page(url='https://test.com')
		assert not await DummyActionPageFilterNegative.is_applicable(page)


class TestActionsController:
	"""Tests the action controller"""

	async def test_get_applicable_actions(self) -> None:
		"""Tests if the applicable actions are returned correctly, i.e. filters are applied correctly."""

		actions_controller = ActionsRegistry([DummyClickTextAction, DummyTypeAction])

		# test with no domains and no page filter
		page = Page(url='https://google.com')
		actions = await actions_controller.get_applicable_actions(page)
		expected_action_count = 2
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_click_text_action'
		assert actions[1].get_action_name() == 'dummy_type_action'

		# test with domains filter (negative)
		page = Page(url='https://google.com')

		class DummyClickCoordActionTest(DummyClickCoordAction):
			domains: ClassVar[list[str] | None] = ['*.test.com']

		actions_controller.register_action(DummyClickCoordActionTest)
		actions = await actions_controller.get_applicable_actions(page)
		expected_action_count = 2
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_click_text_action'
		assert actions[1].get_action_name() == 'dummy_type_action'

		# test with domains filter (positive)
		page = Page(url='https://test.com')
		actions = await actions_controller.get_applicable_actions(page)
		expected_action_count = 3
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_click_text_action'
		assert actions[1].get_action_name() == 'dummy_type_action'
		assert actions[2].get_action_name() == 'dummy_click_coord_action_test'

	async def test_get_applicable_actions_str(self) -> None:
		"""Tests if the applicable actions string is returned correctly."""

		actions_controller = ActionsRegistry([DummyClickTextAction, DummyTypeAction])
		page = Page(url='https://google.com')
		actions_str = await actions_controller.get_applicable_actions_str(page)
		expected_actions_str = (
			"- dummy_click_text_action('text') - Clicks on the first element that contains the given text.\n"
			+ "- dummy_type_action('selector', 'text') - Types text into the focused element."
		)
		assert actions_str == expected_actions_str

	@pytest.mark.skip(reason='This test is not implemented yet. It includes all the default actions from the actions.py file.')
	async def test_create_default(self) -> None:
		"""Tests if the default actions are created correctly."""

		actions_controller = ActionsRegistry.create_default()
		page = Page(url='https://google.com')
		actions_str = await actions_controller.get_applicable_actions_str(page)
		expected_actions_str = (
			'- dummy_click_text_action(text) - Clicks on the first element that contains the given text.\n'
			+ '- dummy_type_action(selector, text) - Types text into the focused element.\n'
			+ '- dummy_click_coord_action(x, y) - Clicks on the given coordinates.'
		)
		assert actions_str == expected_actions_str


class TestActionParser:
	"""Tests the action parser"""

	def test_parse_action_str(self) -> None:
		"""Tests if the action string is parsed correctly."""

		action_parser = ActionParser()

		# test with single argument
		action_str = 'dummy_click_text_action("text")'
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.text == 'text'
		assert action.get_action_name() == 'dummy_click_text_action'

		# test with multiple arguments
		action_str = 'dummy_type_action("selector", "text")'
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.selector == 'selector'
		assert action.text == 'text'
		assert action.get_action_name() == 'dummy_type_action'

		# test with commas and spaces in the arguments
		action_str = 'dummy_type_action("text with spaces and commas, here", "text")'
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.selector == 'text with spaces and commas, here'
		assert action.text == 'text'
		assert action.get_action_name() == 'dummy_type_action'

		# test with spaces around the arguments
		action_str = 'dummy_type_action( "selector" ,  "text"  )'
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.selector == 'selector'
		assert action.text == 'text'
		assert action.get_action_name() == 'dummy_type_action'

		# test with colons in the arguments
		action_str = "dummy_click_text_action('random text with colons: 4 Av-9 St (F)(G), 7 Av (B)(Q), 8 Av (N)...')"
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.text == 'random text with colons: 4 Av-9 St (F)(G), 7 Av (B)(Q), 8 Av (N)...'
		assert action.get_action_name() == 'dummy_click_text_action'

		# test with a quotation mark in the arguments
		action_str = "dummy_click_text_action('random text with a quotation mark \"')"
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.text == 'random text with a quotation mark "'
		assert action.get_action_name() == 'dummy_click_text_action'

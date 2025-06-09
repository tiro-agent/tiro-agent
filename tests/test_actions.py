from collections.abc import Callable
from typing import ClassVar

import pytest
from pydantic import Field

from web_agent.agent.actions import ActionResult, ActionResultStatus, ActionsController, BaseAction


class Page:
	def __init__(self, url: str) -> None:
		self.url = url


class DummyClickTextAction(BaseAction):
	"""Clicks on the first element that contains the given text."""

	text: str = Field(description='The text to click on.')

	def execute(self, page: Page) -> ActionResult:
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message')


class DummyTypeAction(BaseAction):
	"""Types text into the focused element."""

	selector: str = Field(description='The selector to type into.')
	text: str = Field(description='The text to type into the focused element.')

	def execute(self, page: Page) -> ActionResult:
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message 2')


class DummyClickCoordAction(BaseAction):
	"""Clicks on the given coordinates."""

	x: int = Field(description='The x coordinate to click on.')
	y: int = Field(description='The y coordinate to click on.')

	def execute(self, page: Page) -> ActionResult:
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message 3')


class TestBaseAction:
	def test_get_action_name(self) -> None:
		assert DummyClickTextAction.get_action_name() == 'dummy_click_text_action'
		assert DummyTypeAction.get_action_name() == 'dummy_type_action'
		assert DummyClickCoordAction.get_action_name() == 'dummy_click_coord_action'

		class MyLLMAction(BaseAction):
			def execute(self, page: Page) -> ActionResult:
				return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message')

		assert MyLLMAction.get_action_name() == 'my_llm_action'

	def test_is_applicable_domain_filter(self) -> None:
		# test with no domains and no page filter
		class DummyActionNoFilter(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = None
			page_filter: ClassVar[Callable[[Page], bool] | None] = None

		page = Page(url='https://www.google.com')
		assert DummyActionNoFilter.is_applicable(page)

		# test with single domain filter (positive)
		class DummyActionGoogle(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['google.com']

		page = Page(url='https://google.com')
		assert DummyActionGoogle.is_applicable(page)

		page = Page(url='https://www.google.com')
		assert DummyActionGoogle.is_applicable(page)

		class DummyActionWildcardGoogle(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['*.google.com']

		page = Page(url='https://www.google.com')
		assert DummyActionWildcardGoogle.is_applicable(page)

		# test with multiple domains filter (positive)
		class DummyActionMultipleDomains(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['test.com', '*.test.com', '*.google.com']

		page = Page(url='https://test.com')
		assert DummyActionMultipleDomains.is_applicable(page)
		page = Page(url='https://www.test.com')
		assert DummyActionMultipleDomains.is_applicable(page)
		page = Page(url='https://www.google.com')
		assert DummyActionMultipleDomains.is_applicable(page)
		page = Page(url='https://www.test.google.com')
		assert DummyActionMultipleDomains.is_applicable(page)

		# test with domains filter (negative)
		class DummyActionTestDomain(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['*.test.com']

		page = Page(url='https://www.google.com')
		assert not DummyActionTestDomain.is_applicable(page)

		# test with multiple domains filter (negative)
		class DummyActionMultipleDomainsNegative(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = ['test.com', '*.test.com', '*.google.com']

		page = Page(url='https://example.com')
		assert not DummyActionMultipleDomainsNegative.is_applicable(page)

		# test with empty domains filter -> makes it negative for all pages
		class DummyActionEmptyDomains(DummyClickTextAction):
			domains: ClassVar[list[str] | None] = []

		page = Page(url='https://www.google.com')
		assert not DummyActionEmptyDomains.is_applicable(page)

		# test with * domains filter -> should raise an error, is not allowed (to allow for all set domains to None)
		with pytest.raises(ValueError):

			class DummyActionWildcardDomain(DummyClickTextAction):
				domains: ClassVar[list[str] | None] = ['*']

			page = Page(url='https://www.google.com')
			DummyActionWildcardDomain.is_applicable(page)

	def test_is_applicable_page_filter(self) -> None:
		# test with page filter (positive)
		class DummyActionPageFilterPositive(DummyClickTextAction):
			page_filter: ClassVar[Callable[[Page], bool] | None] = lambda page: page.url == 'https://google.com'

		page = Page(url='https://google.com')
		assert DummyActionPageFilterPositive.is_applicable(page)

		# test with page filter (negative)
		class DummyActionPageFilterNegative(DummyClickTextAction):
			page_filter: ClassVar[Callable[[Page], bool] | None] = lambda page: page.url == 'https://google.com'

		page = Page(url='https://test.com')
		assert not DummyActionPageFilterNegative.is_applicable(page)


class TestActionsController:
	def test_get_applicable_actions(self) -> None:
		actions_controller = ActionsController([DummyClickTextAction, DummyTypeAction])

		# test with no domains and no page filter
		page = Page(url='https://google.com')
		actions = actions_controller._get_applicable_actions(page)
		expected_action_count = 2
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_click_text_action'
		assert actions[1].get_action_name() == 'dummy_type_action'

		# test with domains filter (negative)
		page = Page(url='https://google.com')

		class DummyClickCoordActionTest(DummyClickCoordAction):
			domains: ClassVar[list[str] | None] = ['*.test.com']

		actions_controller.register_action(DummyClickCoordActionTest)
		actions = actions_controller._get_applicable_actions(page)
		expected_action_count = 2
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_click_text_action'
		assert actions[1].get_action_name() == 'dummy_type_action'

		# test with domains filter (positive)
		page = Page(url='https://test.com')
		actions = actions_controller._get_applicable_actions(page)
		expected_action_count = 3
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_click_text_action'
		assert actions[1].get_action_name() == 'dummy_type_action'
		assert actions[2].get_action_name() == 'dummy_click_coord_action_test'

	def test_get_applicable_actions_str(self) -> None:
		actions_controller = ActionsController([DummyClickTextAction, DummyTypeAction])
		page = Page(url='https://google.com')
		actions_str = actions_controller.get_applicable_actions_str(page)
		expected_actions_str = (
			'dummy_click_text_action(text) - Clicks on the first element that contains the given text.\n'
			+ 'dummy_type_action(selector, text) - Types text into the focused element.'
		)
		assert actions_str == expected_actions_str

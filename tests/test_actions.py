from collections.abc import Callable
from typing import ClassVar

import pytest

from web_agent.agent.actions import ActionResult, ActionResultStatus, ActionsController, BaseAction


class Page:
	def __init__(self, url: str) -> None:
		self.url = url


class DummyAction(BaseAction):
	selector: str = 'dummy-selector'
	text: str = 'dummy-text'

	def execute(self, page: Page) -> ActionResult:
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message')


class DummyAction2(BaseAction):
	selector: str = 'dummy-selector'

	def execute(self, page: Page) -> ActionResult:
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message 2')


class DummyAction3(BaseAction):
	def execute(self, page: Page) -> ActionResult:
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message 3')


class TestBaseAction:
	def test_get_action_name(self) -> None:
		assert DummyAction.get_action_name() == 'dummy_action'
		assert DummyAction2.get_action_name() == 'dummy_action_2'
		assert DummyAction3.get_action_name() == 'dummy_action_3'

		class MyLLMAction(BaseAction):
			def execute(self, page: Page) -> ActionResult:
				return ActionResult(status=ActionResultStatus.SUCCESS, message='Dummy message')

		assert MyLLMAction.get_action_name() == 'my_llm_action'

	def test_is_applicable_domain_filter(self) -> None:
		# test with no domains and no page filter
		class DummyActionNoFilter(DummyAction):
			domains: ClassVar[list[str] | None] = None
			page_filter: ClassVar[Callable[[Page], bool] | None] = None

		page = Page(url='https://www.google.com')
		assert DummyActionNoFilter.is_applicable(page)

		# test with single domain filter (positive)
		class DummyActionGoogle(DummyAction):
			domains: ClassVar[list[str] | None] = ['google.com']

		page = Page(url='https://google.com')
		assert DummyActionGoogle.is_applicable(page)

		page = Page(url='https://www.google.com')
		assert DummyActionGoogle.is_applicable(page)

		class DummyActionWildcardGoogle(DummyAction):
			domains: ClassVar[list[str] | None] = ['*.google.com']

		page = Page(url='https://www.google.com')
		assert DummyActionWildcardGoogle.is_applicable(page)

		# test with multiple domains filter (positive)
		class DummyActionMultipleDomains(DummyAction):
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
		class DummyActionTestDomain(DummyAction):
			domains: ClassVar[list[str] | None] = ['*.test.com']

		page = Page(url='https://www.google.com')
		assert not DummyActionTestDomain.is_applicable(page)

		# test with multiple domains filter (negative)
		class DummyActionMultipleDomainsNegative(DummyAction):
			domains: ClassVar[list[str] | None] = ['test.com', '*.test.com', '*.google.com']

		page = Page(url='https://example.com')
		assert not DummyActionMultipleDomainsNegative.is_applicable(page)

		# test with empty domains filter -> makes it negative for all pages
		class DummyActionEmptyDomains(DummyAction):
			domains: ClassVar[list[str] | None] = []

		page = Page(url='https://www.google.com')
		assert not DummyActionEmptyDomains.is_applicable(page)

		# test with * domains filter -> should raise an error, is not allowed (to allow for all set domains to None)
		with pytest.raises(ValueError):

			class DummyActionWildcardDomain(DummyAction):
				domains: ClassVar[list[str] | None] = ['*']

			page = Page(url='https://www.google.com')
			DummyActionWildcardDomain.is_applicable(page)

	def test_is_applicable_page_filter(self) -> None:
		# test with page filter (positive)
		class DummyActionPageFilterPositive(DummyAction):
			page_filter: ClassVar[Callable[[Page], bool] | None] = lambda page: page.url == 'https://google.com'

		page = Page(url='https://google.com')
		assert DummyActionPageFilterPositive.is_applicable(page)

		# test with page filter (negative)
		class DummyActionPageFilterNegative(DummyAction):
			page_filter: ClassVar[Callable[[Page], bool] | None] = lambda page: page.url == 'https://google.com'

		page = Page(url='https://test.com')
		assert not DummyActionPageFilterNegative.is_applicable(page)


class TestActionsController:
	def test_get_applicable_actions(self) -> None:
		actions_controller = ActionsController([DummyAction, DummyAction2])

		# test with no domains and no page filter
		page = Page(url='https://google.com')
		actions = actions_controller._get_applicable_actions(page)
		expected_action_count = 2
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_action'
		assert actions[1].get_action_name() == 'dummy_action_2'

		# test with domains filter (negative)
		page = Page(url='https://google.com')

		class DummyAction3Test(DummyAction3):
			domains: ClassVar[list[str] | None] = ['*.test.com']

		actions_controller.register_action(DummyAction3Test)
		actions = actions_controller._get_applicable_actions(page)
		expected_action_count = 2
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_action'
		assert actions[1].get_action_name() == 'dummy_action_2'

		# test with domains filter (positive)
		page = Page(url='https://test.com')
		actions = actions_controller._get_applicable_actions(page)
		expected_action_count = 3
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_action'
		assert actions[1].get_action_name() == 'dummy_action_2'
		assert actions[2].get_action_name() == 'dummy_action_3_test'

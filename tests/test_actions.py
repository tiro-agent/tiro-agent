from collections.abc import Callable
from typing import ClassVar

import pytest
from pydantic import Field

from web_agent.agent.actions import ActionParser, ActionResult, ActionResultStatus, ActionsController, BaseAction


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
		actions = actions_controller.get_applicable_actions(page)
		expected_action_count = 2
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_click_text_action'
		assert actions[1].get_action_name() == 'dummy_type_action'

		# test with domains filter (negative)
		page = Page(url='https://google.com')

		class DummyClickCoordActionTest(DummyClickCoordAction):
			domains: ClassVar[list[str] | None] = ['*.test.com']

		actions_controller.register_action(DummyClickCoordActionTest)
		actions = actions_controller.get_applicable_actions(page)
		expected_action_count = 2
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_click_text_action'
		assert actions[1].get_action_name() == 'dummy_type_action'

		# test with domains filter (positive)
		page = Page(url='https://test.com')
		actions = actions_controller.get_applicable_actions(page)
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
			"dummy_click_text_action('text') - Clicks on the first element that contains the given text.\n"
			+ "dummy_type_action('selector', 'text') - Types text into the focused element."
		)
		assert actions_str == expected_actions_str

	@pytest.mark.skip(reason='This test is not implemented yet. It includes all the default actions from the actions.py file.')
	def test_create_default(self) -> None:
		actions_controller = ActionsController.create_default()
		page = Page(url='https://google.com')
		actions_str = actions_controller.get_applicable_actions_str(page)
		expected_actions_str = (
			'dummy_click_text_action(text) - Clicks on the first element that contains the given text.\n'
			+ 'dummy_type_action(selector, text) - Types text into the focused element.'
			+ 'dummy_click_coord_action(x, y) - Clicks on the given coordinates.'
		)
		assert actions_str == expected_actions_str


class TestActionParser:
	def test_is_valid_action_function(self) -> None:
		assert ActionParser._is_valid_action_function('click_by_text("text")')
		assert ActionParser._is_valid_action_function('click_by_text_ith("text", 1)')
		assert ActionParser._is_valid_action_function('back()')
		assert ActionParser._is_valid_action_function('finish("answer")')
		assert ActionParser._is_valid_action_function('click_text("hello (this is a test)")')

		# test with invalid function calls
		assert not ActionParser._is_valid_action_function('click_by_text("text")(')
		assert not ActionParser._is_valid_action_function('click_by_text("text"')
		assert not ActionParser._is_valid_action_function('click_by_text')

	def test_parse_comma_separated_params(self) -> None:
		assert ActionParser._parse_comma_separated_params('"text"') == ['"text"']
		assert ActionParser._parse_comma_separated_params('"text, text"') == ['"text, text"']
		assert ActionParser._parse_comma_separated_params('"text, text", "2"') == ['"text, text"', '"2"']
		assert ActionParser._parse_comma_separated_params('\'text, text\', "2"') == ["'text, text'", '"2"']
		assert ActionParser._parse_comma_separated_params('2') == ['2']

	def test_parse_parameter_value(self) -> None:
		# test with quotes
		assert ActionParser._parse_parameter_value('"text"') == 'text'
		assert ActionParser._parse_parameter_value("'text'") == 'text'

		# test with spaces
		assert ActionParser._parse_parameter_value(' "text" ') == 'text'

		# test with comma in string
		assert ActionParser._parse_parameter_value('text, text') == 'text, text'

		# test with numbers
		assert ActionParser._parse_parameter_value('1') == 1
		assert ActionParser._parse_parameter_value('1.0') == 1.0

		# test with named parameters and equal sign
		assert ActionParser._parse_parameter_value('test="hello"') == 'hello'
		assert ActionParser._parse_parameter_value('test= "hello"') == 'hello'
		assert ActionParser._parse_parameter_value('test ="hello"') == 'hello'
		assert ActionParser._parse_parameter_value('test = "hello"') == 'hello'
		assert ActionParser._parse_parameter_value("test='hello'") == 'hello'
		assert ActionParser._parse_parameter_value("test='1'") == 1
		assert ActionParser._parse_parameter_value('test=1') == 1

		# test with named parameters and colon
		assert ActionParser._parse_parameter_value('test: 1') == 1
		assert ActionParser._parse_parameter_value('test: 1.0') == 1.0
		assert ActionParser._parse_parameter_value('test: hello') == 'hello'
		assert ActionParser._parse_parameter_value('test: "hello"') == 'hello'

	def test_parse_action_str(self) -> None:
		action_parser = ActionParser()
		action_str = 'dummy_click_text_action("text")'
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.text == 'text'
		assert action.get_action_name() == 'dummy_click_text_action'

		action_str = 'dummy_type_action("selector", "text")'
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.selector == 'selector'
		assert action.text == 'text'
		assert action.get_action_name() == 'dummy_type_action'

		action_str = "dummy_click_text_action('random text with colons: 4 Av-9 St (F)(G), 7 Av (B)(Q), 8 Av (N)...')"
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.text == 'random text with colons: 4 Av-9 St (F)(G), 7 Av (B)(Q), 8 Av (N)...'
		assert action.get_action_name() == 'dummy_click_text_action'

		action_str = "dummy_click_text_action('random text with a quotation mark \"')"
		action = action_parser.parse(action_str, [DummyClickTextAction, DummyTypeAction])
		assert action.text == 'random text with a quotation mark "'
		assert action.get_action_name() == 'dummy_click_text_action'

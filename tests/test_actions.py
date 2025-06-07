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
		action = DummyAction(domains=['google.com'])
		page = Page(url='https://google.com')
		assert action.is_applicable(page)

		action = DummyAction(domains=['google.com'])
		page = Page(url='https://www.google.com')
		assert action.is_applicable(page)

		action = DummyAction(domains=['*.google.com'])
		page = Page(url='https://www.google.com')
		assert action.is_applicable(page)

		# test with multiple domains filter (positive)
		action = DummyAction(domains=['test.com', '*.test.com', '*.google.com'])
		page = Page(url='https://test.com')
		assert action.is_applicable(page)
		page = Page(url='https://www.test.com')
		assert action.is_applicable(page)
		page = Page(url='https://www.google.com')
		assert action.is_applicable(page)
		page = Page(url='https://www.test.google.com')
		assert action.is_applicable(page)

		# test with domains filter (negative)
		action = DummyAction(domains=['*.test.com'])
		page = Page(url='https://www.google.com')
		assert not action.is_applicable(page)

		# test with multiple domains filter (negative)
		action = DummyAction(domains=['test.com', '*.test.com', '*.google.com'])
		page = Page(url='https://example.com')
		assert not action.is_applicable(page)

	def test_is_applicable_page_filter(self) -> None:
		# test with page filter (positive)
		action = DummyAction(page_filter=lambda page: page.url == 'https://google.com')
		page = Page(url='https://google.com')
		assert action.is_applicable(page)

		# test with page filter (negative)
		action = DummyAction(page_filter=lambda page: page.url == 'https://google.com')
		page = Page(url='https://test.com')
		assert not action.is_applicable(page)


class TestActionsController:
	def test_get_applicable_actions(self) -> None:
		actions_controller = ActionsController([DummyAction(), DummyAction2()])

		# test with no domains and no page filter
		page = Page(url='https://google.com')
		actions = actions_controller._get_applicable_actions(page)
		expected_action_count = 2
		assert len(actions) == expected_action_count
		assert actions[0].get_action_name() == 'dummy_action'
		assert actions[1].get_action_name() == 'dummy_action_2'

		# test with domains filter (negative)
		page = Page(url='https://google.com')
		actions_controller.register_action(DummyAction3(domains=['*.test.com']))
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
		assert actions[2].get_action_name() == 'dummy_action_3'

	def test_get_agent_decision_type_one_action(self) -> None:
		actions_controller = ActionsController([DummyAction()])
		page = Page(url='https://google.com')
		agent_decision_type = actions_controller.get_agent_decision_type(page)
		assert agent_decision_type.model_json_schema(mode='serialization') == {
			'$defs': {
				'DummyAction': {
					'properties': {
						'selector': {'default': 'dummy-selector', 'title': 'Selector', 'type': 'string'},
						'text': {'default': 'dummy-text', 'title': 'Text', 'type': 'string'},
					},
					'title': 'DummyAction',
					'type': 'object',
				},
			},
			'properties': {
				'thought': {'description': 'Your reasoning process and next step.', 'title': 'Thought', 'type': 'string'},
				'action': {'$ref': '#/$defs/DummyAction', 'description': 'The action to perform next, chosen from the available tools.'},
			},
			'required': ['thought', 'action'],
			'title': 'AgentDecision',
			'type': 'object',
		}

	def test_get_agent_decision_type_one_action_on_page_with_domains_filter(self) -> None:
		actions_controller = ActionsController([DummyAction(), DummyAction2(domains=['*.test.com'])])
		page = Page(url='https://google.com')
		agent_decision_type = actions_controller.get_agent_decision_type(page)
		assert agent_decision_type.model_json_schema(mode='serialization') == {
			'$defs': {
				'DummyAction': {
					'properties': {
						'selector': {'default': 'dummy-selector', 'title': 'Selector', 'type': 'string'},
						'text': {'default': 'dummy-text', 'title': 'Text', 'type': 'string'},
					},
					'title': 'DummyAction',
					'type': 'object',
				},
			},
			'properties': {
				'thought': {'description': 'Your reasoning process and next step.', 'title': 'Thought', 'type': 'string'},
				'action': {'$ref': '#/$defs/DummyAction', 'description': 'The action to perform next, chosen from the available tools.'},
			},
			'required': ['thought', 'action'],
			'title': 'AgentDecision',
			'type': 'object',
		}

	def test_get_agent_decision_type_two_actions(self) -> None:
		actions_controller = ActionsController([DummyAction(), DummyAction2()])
		page = Page(url='https://google.com')
		agent_decision_type = actions_controller.get_agent_decision_type(page)
		assert agent_decision_type.model_json_schema(mode='serialization') == {
			'$defs': {
				'DummyAction': {
					'properties': {
						'selector': {'default': 'dummy-selector', 'title': 'Selector', 'type': 'string'},
						'text': {'default': 'dummy-text', 'title': 'Text', 'type': 'string'},
					},
					'title': 'DummyAction',
					'type': 'object',
				},
				'DummyAction2': {
					'properties': {
						'selector': {'default': 'dummy-selector', 'title': 'Selector', 'type': 'string'},
					},
					'title': 'DummyAction2',
					'type': 'object',
				},
			},
			'properties': {
				'thought': {'description': 'Your reasoning process and next step.', 'title': 'Thought', 'type': 'string'},
				'action': {
					'anyOf': [
						{'$ref': '#/$defs/DummyAction'},
						{'$ref': '#/$defs/DummyAction2'},
					],
					'description': 'The action to perform next, chosen from the available tools.',
					'title': 'Action',
				},
			},
			'required': ['thought', 'action'],
			'title': 'AgentDecision',
			'type': 'object',
		}

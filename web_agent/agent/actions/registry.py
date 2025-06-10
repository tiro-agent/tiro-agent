from playwright.sync_api import Page

# Import all actions to make sure they're loaded for __subclasses__() to work
from web_agent.agent.actions import actions as _  # noqa: F401
from web_agent.agent.actions.base import BaseAction
from web_agent.agent.actions.parser import ActionParser


class ActionsRegistry:
	"""Registry for actions."""

	def __init__(self, actions: list[type[BaseAction]] | None = None) -> None:
		self.actions = actions if actions is not None else []
		self.parser = ActionParser()

	@classmethod
	def create_default(cls) -> 'ActionsRegistry':
		"""Creates an ActionsRegistry with default actions only."""
		return cls(actions=BaseAction.get_default_actions())

	@classmethod
	def create_all(cls) -> 'ActionsRegistry':
		"""Creates an ActionsRegistry with all available actions."""
		return cls(actions=BaseAction.__subclasses__())

	def register_action(self, action: type[BaseAction]) -> None:
		self.actions.append(action)

	def get_applicable_actions(self, page: Page) -> list[type[BaseAction]]:
		return [action for action in self.actions if action.is_applicable(page)]

	def get_applicable_actions_str(self, page: Page) -> str:
		return '\n'.join([action.get_action_definition_str() for action in self.get_applicable_actions(page)])

	def parse_action_str(self, action_str: str) -> BaseAction:
		"""Parse an action string into a BaseAction instance."""
		return self.parser.parse(action_str, self.actions)

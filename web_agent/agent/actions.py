import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from urllib.parse import urlparse

from playwright.sync_api import Page
from pydantic import BaseModel, Field
from utils import matches_domain_pattern


class ActionResultStatus(str, Enum):
	SUCCESS = 'success'
	FAILURE = 'failure'
	INFO = 'info'


class ActionResult(BaseModel):
	"""Represents the outcome of an executed action."""

	status: ActionResultStatus = Field(..., description='The status of the action (e.g., "success", "failure", "info").')
	message: str = Field(..., description='A detailed message about the outcome.')
	data: dict = Field(default_factory=dict, description='Optional: Additional structured data from the action.')


class BaseAction(BaseModel, ABC):
	"""
	An abstract class for all actions.
	The docstring of this class will be the tool's description for the LLM.
	Its fields will be the tool's parameters.
	"""

	# Filters for applicability
	domains: list[str] | None = Field(
		None, description='List of domain patterns (e.g., "*.google.com", "example.com") where this tool is applicable.'
	)
	page_filter: Callable[[Page], bool] | None = Field(
		None,
		exclude=True,
		description='A callable function that returns True if the tool is applicable to the given Page object.',
	)

	@abstractmethod
	def execute(self, page: Page) -> ActionResult:
		"""Abstract method to be implemented by subclasses."""
		pass

	@classmethod
	def get_action_name(cls) -> str:
		"""Returns the snake_case name of the action from its class name."""
		# E.g., ClickAction -> click_action, TypeAction -> type_action
		name = cls.__name__.replace('Action', '').lower()
		return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

	def is_applicable(self, page: Page) -> bool:
		if self.domains is not None:
			domain = urlparse(page.url).netloc
			if not any(matches_domain_pattern(domain, pattern) for pattern in self.domains):
				# print(f'DEBUG: Tool "{self.get_tool_name()}" not applicable: Domain "{current_domain}" not in allowed {self.domains}')
				return False
		if self.page_filter is not None and not self.page_filter(page):
			# print(f'DEBUG: Tool "{self.get_tool_name()}" not applicable: Page filter returned False for "{page.url}"')
			return False
		return True


class ClickAction(BaseAction):
	"""Clicks a specific element on the page."""

	selector: str = Field(description='The selector to click on.')

	def execute(self, page: Page) -> ActionResult:
		"""Click on the first element that contains the given text."""
		targets = page.get_by_text(self.selector).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() == 1:
			targets.click()
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the first element that contains the given text.')
		else:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple targets found: ' + str(targets.all()))

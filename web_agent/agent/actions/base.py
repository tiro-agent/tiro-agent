import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar
from urllib.parse import urlparse

from playwright.async_api import Page
from pydantic import BaseModel, Field

from web_agent.agent.schemas import Task
from web_agent.utils import check_domain_pattern_match


class ActionResultStatus(str, Enum):
	SUCCESS = 'success'
	FAILURE = 'failure'
	UNKNOWN = 'unknown'
	INFO = 'info'
	ABORT = 'abort'
	FINISH = 'finish'


class ActionResult(BaseModel):
	"""Represents the outcome of an executed action."""

	status: ActionResultStatus = Field(description='The status of the action (e.g., "success", "failure", "info", "abort", "finish").')
	message: str = Field(description='A detailed message about the outcome.')
	data: dict = Field(default_factory=dict, description='Optional: Additional structured data from the action.')


class ActionContext(BaseModel):
	"""Represents the context for the action execution."""

	page: Page
	task: Task

	model_config = {
		'arbitrary_types_allowed': True,
	}


class BaseAction(BaseModel, ABC):
	"""
	An abstract class for all actions.
	The docstring of this class will be the tool's description for the LLM.
	Its fields will be the tool's parameters.
	"""

	# Filters for applicability
	domains: ClassVar[list[str] | None] = None

	@classmethod
	async def page_filter(cls, page: Page) -> bool:
		"""
		Default page filter that always returns True, meaning no specific page filtering is applied.
		Subclasses can override this method to add custom page-based applicability logic.
		"""
		return True

	@abstractmethod
	async def execute(self, context: ActionContext) -> ActionResult:
		"""Abstract method to be implemented by subclasses."""
		pass

	@classmethod
	def get_action_name(cls) -> str:
		"""Returns the snake_case name of the action from its class name."""
		# E.g., Click -> click, Type -> type, MyHTTP -> my_http, MyAction2 -> my_action_2 (not my_2)
		name = cls.__name__
		s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
		s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1)
		return re.sub(r'([a-zA-Z])([0-9])', r'\1_\2', s2).lower()

	@classmethod
	async def is_applicable(cls, page: Page) -> bool:
		if cls.domains is not None:
			domain = urlparse(await page.url).netloc
			if not any(check_domain_pattern_match(domain, pattern) for pattern in cls.domains):
				return False
		if not await cls.page_filter(page):
			return False
		return True

	@classmethod
	def get_action_type_str(cls) -> str:
		# example: click_by_text('text')
		return f'{cls.get_action_name()}({", ".join(f"'{name}'" for name in cls.model_fields.keys())})'

	@classmethod
	def get_action_description(cls) -> str:
		return cls.__doc__

	@classmethod
	def get_action_definition_str(cls) -> str:
		return f'{cls.get_action_type_str()} - {cls.get_action_description()}'

	def get_action_str(self) -> str:
		return f'{self.get_action_name()}({", ".join(f"{name}='{value}'" for name, value in self.model_dump().items())})'

	@classmethod
	def is_default_action(cls) -> bool:
		"""Check if this action is marked as a default action."""
		return getattr(cls, '_is_default_action', False)

	@classmethod
	def get_default_actions(cls) -> list[type['BaseAction']]:
		"""Get all action subclasses that are marked as default actions."""

		def get_all_subclasses(cls: type['BaseAction']) -> set[type['BaseAction']]:
			"""Recursively get all subclasses."""
			result = set()
			for subclass in cls.__subclasses__():
				result.add(subclass)
				result.update(get_all_subclasses(subclass))
			return result

		all_subclasses = get_all_subclasses(cls)
		return [action for action in all_subclasses if action.is_default_action()]


def default_action(cls: type['BaseAction']) -> type['BaseAction']:
	"""Decorator to mark an action as a default action that should be included in the default registry."""
	cls._is_default_action = True
	return cls

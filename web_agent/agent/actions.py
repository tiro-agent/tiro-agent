import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import ClassVar, Union
from urllib.parse import urlparse

from playwright.sync_api import Page
from pydantic import BaseModel, Field, create_model

from web_agent.utils import check_domain_pattern_match


class ActionResultStatus(str, Enum):
	SUCCESS = 'success'
	FAILURE = 'failure'
	INFO = 'info'
	ABORT = 'abort'
	FINISH = 'finish'


class ActionResult(BaseModel):
	"""Represents the outcome of an executed action."""

	status: ActionResultStatus = Field(..., description='The status of the action (e.g., "success", "failure", "info", "abort", "finish").')
	message: str = Field(..., description='A detailed message about the outcome.')
	data: dict = Field(default_factory=dict, description='Optional: Additional structured data from the action.')


class BaseAction(BaseModel, ABC):
	"""
	An abstract class for all actions.
	The docstring of this class will be the tool's description for the LLM.
	Its fields will be the tool's parameters.
	"""

	# Filters for applicability
	domains: ClassVar[list[str] | None] = None
	page_filter: ClassVar[Callable[[Page], bool] | None] = None

	@abstractmethod
	def execute(self, page: Page) -> ActionResult:
		"""Abstract method to be implemented by subclasses."""
		pass

	@classmethod
	def get_action_name(cls) -> str:
		"""Returns the snake_case name of the action from its class name."""
		# E.g., ClickAction -> click_action, TypeAction -> type_action, MyHTTPAction -> my_http_action, MyAction2 -> my_action_2
		name = cls.__name__
		s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
		s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1)
		return re.sub(r'([a-zA-Z])([0-9])', r'\1_\2', s2).lower()

	@classmethod
	def is_applicable(cls, page: Page) -> bool:
		if cls.domains is not None:
			domain = urlparse(page.url).netloc
			if not any(check_domain_pattern_match(domain, pattern) for pattern in cls.domains):
				return False
		if cls.page_filter is not None and not cls.page_filter(page):
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


class TypeAction(BaseAction):
	"""Types text into a specific element on the page, like an input field."""

	selector: str = Field(description='A selector for the input field.')
	text: str = Field(description='The text to type into the input field.')

	def execute(self, page: Page) -> ActionResult:
		"""Type text into an element."""
		try:
			targets = page.locator(self.selector).filter(visible=True)
			if targets.count() == 0:
				return ActionResult(status=ActionResultStatus.FAILURE, message='Input field not found on page')
			elif targets.count() == 1:
				targets.fill(self.text)
				return ActionResult(status=ActionResultStatus.SUCCESS, message=f"Typed '{self.text}' into element '{self.selector}'.")
			else:
				return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple input fields found: ' + str(targets.all()))
		except Exception as e:
			return ActionResult(
				status=ActionResultStatus.FAILURE,
				message=f"Could not type into element with selector '{self.selector}': {e}",
			)


class AbortAction(BaseAction):
	"""
	Abort the task only in case when you have failed to complete the task and there is no way to recover.
	Do not use this if you have completed the task.
	"""

	reason: str = Field(description='The reason for aborting the task.')

	def execute(self, page: Page) -> ActionResult:
		"""Abort the task."""
		return ActionResult(status=ActionResultStatus.ABORT, message='Task aborted.')


class FinishAction(BaseAction):
	"""Indicate that the task is finished and provide the final answer."""

	answer: str = Field(description='The final answer to the user query.')

	def execute(self, page: Page) -> ActionResult:
		"""Finish the task."""
		return ActionResult(
			status=ActionResultStatus.FINISH,
			message=f'Task finished. The answer is: {self.answer}',
			data={'answer': self.answer},
		)


class ActionsController:
	"""Controller for actions."""

	def __init__(self, actions: list[type[BaseAction]] | None = None) -> None:
		self.actions = actions if actions is not None else []

	@classmethod
	def create_default(cls) -> 'ActionsController':
		"""Creates an ActionsController with all available actions."""
		return cls(actions=BaseAction.__subclasses__())

	def register_action(self, action: type[BaseAction]) -> None:
		self.actions.append(action)

	def _get_applicable_actions(self, page: Page) -> list[type[BaseAction]]:
		return [action for action in self.actions if action.is_applicable(page)]

	def get_agent_decision_type(self, page: Page) -> type[BaseModel]:
		"""Get the type of the agent decision which will be used to parse the agent's response."""
		applicable_action_types = self._get_applicable_actions(page)
		if not applicable_action_types:
			# there should always be at least one applicable action (like finish action, abort action, etc.)
			raise ValueError('No applicable actions provided')

		action_union = Union[tuple(applicable_action_types)]  # noqa: UP007

		return create_model(
			'AgentDecision',
			thought=(str, Field(..., description='Your reasoning process and next step.')),
			action=(
				action_union,
				Field(..., description='The action to perform next, chosen from the available tools.'),
			),
		)

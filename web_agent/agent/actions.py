import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import ClassVar
from urllib.parse import urlparse

from playwright.sync_api import Page
from pydantic import BaseModel, Field

from web_agent.agent.schema import Task
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
	def execute(self, page: Page, task: Task) -> ActionResult:
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
	def is_applicable(cls, page: Page) -> bool:
		if cls.domains is not None:
			domain = urlparse(page.url).netloc
			if not any(check_domain_pattern_match(domain, pattern) for pattern in cls.domains):
				return False
		if cls.page_filter is not None and not cls.page_filter(page):
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
		return f'{self.get_action_name()}({", ".join(f"{name}: {value}" for name, value in self.model_dump().items())})'


class Click(BaseAction):
	"""Clicks a specific element on the page."""

	selector: str = Field(description='The selector to click on.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Click on the first element that contains the given text."""
		targets = page.get_by_text(self.selector).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() == 1:
			targets.click()
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the first element that contains the given text.')
		else:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple targets found: ' + str(targets.all()))


class ClickByText(BaseAction):
	"""Clicks on the first element that contains the given text."""

	text: str = Field(description='The text to click on.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Click on the first element that contains the given text."""
		targets = page.get_by_text(self.text).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() == 1:
			targets.click()
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the first element that contains the given text.')
		else:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple targets found: ' + str(targets.all()))


class ClickByTextIth(BaseAction):
	"""Clicks on the ith element that contains the given text."""

	text: str = Field(description='The text to click on.')
	ith: int = Field(description='The index of the element to click on.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Click on the ith element that contains the given text."""
		targets = page.get_by_text(self.text).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() < self.ith:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Not enough targets found: ' + str(targets.all()))
		else:
			targets[self.ith].click()
			return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the ith element that contains the given text.')


class ScrollUp(BaseAction):
	"""Scrolls up on the page."""

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Scrolls up on the page."""
		page.mouse.wheel(0, -700)
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Scrolled up on the page.')


class ScrollDown(BaseAction):
	"""Scrolls down on the page."""

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Scrolls down on the page."""
		page.mouse.wheel(0, 700)
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Scrolled down on the page.')


class SearchText(BaseAction):
	"""Searches for the given text on the current page and focuses on it."""

	text: str = Field(description='The text to search for.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Searches for the given query on the current page and focuses on it."""
		targets = page.get_by_text(self.text).filter(visible=True)
		if targets.count() == 0:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Text not found on page')
		elif targets.count() == 1:
			targets.focus()
			return ActionResult(
				status=ActionResultStatus.SUCCESS, message='Searched for the given text on the current page and focused on it.'
			)
		else:
			return ActionResult(status=ActionResultStatus.FAILURE, message='Multiple targets found: ' + str(targets.all()))


class Type(BaseAction):
	"""Type text into the focused element."""

	text: str = Field(description='The text to type into the focused element.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Type text into an element."""
		try:
			page.keyboard.type(self.text)
			return ActionResult(status=ActionResultStatus.SUCCESS, message=f"Typed '{self.text}' into the focused element.")
		except Exception as e:
			return ActionResult(
				status=ActionResultStatus.FAILURE,
				message=f'Could not type into the focused element: {e}',
			)


class Fill(BaseAction):
	"""Fill the given input text into the first element that has the given placeholder text."""

	placeholder: str = Field(description='The placeholder text of the input field.')
	text: str = Field(description='The text to fill into the input field.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Fill the given input text into the first element that has the given placeholder text."""
		page.locator(f'input[placeholder="{self.placeholder}"]').fill(self.text)
		return ActionResult(
			status=ActionResultStatus.SUCCESS, message=f"Filled '{self.text}' into the first element that has the given placeholder text."
		)


class ClickCoord(BaseAction):
	"""Clicks on the given coordinates."""

	x: int = Field(description='The x coordinate to click on.')
	y: int = Field(description='The y coordinate to click on.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Click on the given coordinates."""
		page.mouse.click(self.x, self.y)
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Clicked on the given coordinates.')


class Back(BaseAction):
	"""Go back to the previous page."""

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Go back to the previous page."""
		page.go_back()
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Go back to the previous page.')


class Reset(BaseAction):
	"""Reset the browser to the initial starting page."""

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Reset the browser to the initial starting page."""
		page.goto(task.url)
		return ActionResult(status=ActionResultStatus.SUCCESS, message='Reset the browser to the initial starting page.')


class Abort(BaseAction):
	"""Abort the task only in case when you have failed to complete the task and there is no way to recover."""

	reason: str = Field(description='The reason for aborting the task.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Abort the task."""
		return ActionResult(status=ActionResultStatus.ABORT, message=f'Task aborted. Reason: {self.reason}')


class Finish(BaseAction):
	"""Indicate that the task is finished and provide the final answer."""

	answer: str = Field(description='The final answer to the user query.')

	def execute(self, page: Page, task: Task) -> ActionResult:
		"""Finish the task."""
		return ActionResult(
			status=ActionResultStatus.FINISH,
			message=f'Task finished. The answer is: {self.answer}',
			data={'answer': self.answer},
		)


class ActionDecision(BaseModel):
	"""The decision of the agent."""

	thought: str = Field(..., description='Your reasoning process and next step.')
	action: str = Field(
		...,
		description="The function call to the action to perform next, chosen from the available actions. Example: click_by_text('text')",
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

	def get_applicable_actions_str(self, page: Page) -> str:
		return '\n'.join([action.get_action_definition_str() for action in self._get_applicable_actions(page)])

	def parse_action_str(self, action_str: str) -> BaseAction:
		action_str = self._clean_and_validate_action_str(action_str)

		action_name = action_str.split('(')[0]
		action_type = self._get_action_by_name(action_name)

		if action_type is None:
			raise ValueError(f'Action type not found: {action_name}')

		action_params_str = action_str.split('(')[1].split(')')[0]
		action_params = []
		if action_params_str.strip():  # Only parse if there are parameters
			raw_params = self._parse_comma_separated_params(action_params_str)
			action_params = [self._parse_parameter_value(param) for param in raw_params]

		# Create the action
		if action_params:
			# Map positional parameters to field names
			field_names = list(action_type.model_fields.keys())
			if len(action_params) > len(field_names):
				raise ValueError(f'Too many parameters: expected {len(field_names)}, got {len(action_params)}')

			# Convert parameters to the correct types based on field annotations
			action_kwargs = {}
			for i, param in enumerate(action_params):
				field_name = field_names[i]

				action_kwargs[field_name] = param

			action = action_type(**action_kwargs)
		else:
			action = action_type()

		# Return the action
		return action

	def _get_action_by_name(self, name: str) -> type[BaseAction] | None:
		for action in self.actions:
			if action.get_action_name() == name:
				return action
		return None

	def _get_applicable_actions(self, page: Page) -> list[type[BaseAction]]:
		return [action for action in self.actions if action.is_applicable(page)]

	@classmethod
	def _clean_and_validate_action_str(cls, action_str: str) -> str:
		"""Clean and validate the action string."""
		action_str = action_str.strip()
		if action_str == '':
			raise ValueError('Action string is empty')

		# check if the action has brackets, if not add them
		if '(' not in action_str:
			action_str = f'{action_str}()'

		if not cls._is_valid_action_function(action_str):
			raise ValueError(f'Action string is not valid: {action_str}')

		return action_str

	@staticmethod
	def _is_valid_action_function(action_str: str) -> bool:
		return re.match(r'^[a-zA-Z0-9_]+\([^)]*\)$', action_str)

	@staticmethod
	def _parse_comma_separated_params(param_str: str) -> list[str]:
		"""Parse a comma-separated parameter string, handling quoted strings that may contain commas and named parameters."""
		result = []
		current = ''
		in_quotes = False
		quote_char = None
		for char in param_str:
			if char in ['"', "'"]:
				if not in_quotes:
					in_quotes = True
					quote_char = char
				elif char == quote_char:
					in_quotes = False
				current += char
			elif char == ',' and not in_quotes:
				result.append(current.strip())
				current = ''
			else:
				current += char
		if current:
			result.append(current.strip())
		return result

	@staticmethod
	def _parse_parameter_value(param: str) -> str | int | float:
		"""Parse a parameter value, handling different quote styles and types."""
		param = param.strip()

		# Handle named parameters in the format key=value
		if '=' in param:
			_, value = param.split('=', 1)
			param = value.strip()

		# Handle named parameters in the format key: value
		elif ':' in param:
			_, value = param.split(':', 1)
			param = value.strip()

		# Remove quotes if present
		if len(param) >= 2 and param[0] in ('"', "'") and param[0] == param[-1]:  # noqa: PLR2004
			param = param[1:-1]

		# Try to parse as number (int first, then float)
		for converter in (int, float):
			try:
				return converter(param)
			except ValueError:
				continue

		return param


class ActionHistoryStep(BaseModel):
	"""The step of the action history."""

	action: BaseAction = Field(..., description='The action that was performed.')
	status: ActionResultStatus = Field(..., description='The status of the action.')
	message: str = Field(..., description='The message from the action.')
	screenshot: str = Field(..., description='The path to the screenshot of the action.')


class ActionHistoryController:
	"""Controller for the action history."""

	def __init__(self) -> None:
		self.action_history: list[ActionHistoryStep] = []

	def add_action(self, action: ActionHistoryStep) -> None:
		self.action_history.append(action)

	def get_action_history(self) -> list[ActionHistoryStep]:
		return self.action_history

	def get_action_history_str(self) -> str:
		return 'Prior actions: \n- ' + '\n- '.join(
			[
				f'ACTION: {step.action.get_action_str()}, [{step.status.value.capitalize()}]{
					", MESSAGE: " + step.message if step.status is not ActionResultStatus.SUCCESS else ""
				}'
				for step in self.action_history
			]
		)

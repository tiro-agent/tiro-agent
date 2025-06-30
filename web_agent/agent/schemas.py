from enum import Enum

from pydantic import BaseModel, Field


class Task(BaseModel):
	"""The task to be completed."""

	identifier: str = Field(description='The id of the task.')
	description: str = Field(description='The task to be completed.')
	url: str = Field(description='The url to be loaded.')
	level: str = Field(description='The level of the task.', enum=['easy', 'medium', 'hard'])
	number: int = Field(description='The number of the task.')
	reference_length: int = Field(description='The reference length of the task.')


class AgentDecision(BaseModel):
	"""The decision of the agent which action/function call to perform next."""

	thought: str = Field(description='Your reasoning process and next step.')
	action: str = Field(
		description="The function call to the action to perform next, chosen from the available actions. Example: click_by_text('text')"
	)


class SpecialAgentErrors(Enum):
	"""Special errors that the agent can encounter."""

	URL_LOAD_ERROR = 'URL_LOAD_ERROR'
	STEP_LIMIT_REACHED = 'STEP_LIMIT_REACHED'
	API_TOO_MANY_ERRORS = 'API_TOO_MANY_ERRORS'
	ACTION_PARSING_ERROR = 'ACTION_PARSING_ERROR'
	URL_BLOCKED = 'URL_BLOCKED'
	LLM_ERROR = 'LLM_ERROR'


class AgentErrors(Enum):
	"""Errors that the agent can encounter."""

	CLICK_ERROR = 'CLICK_ERROR'
	SCROLL_ERROR = 'SCROLL_ERROR'
	OPTION_SELECTION_ERROR = 'OPTION_SELECTION_ERROR'
	INPUT_ERROR = 'INPUT_ERROR'  # includes search errors
	NAVIGATION_ERROR = 'NAVIGATION_ERROR'
	FILTER_ERROR = 'FILTER_ERROR'
	OTHER = 'OTHER'

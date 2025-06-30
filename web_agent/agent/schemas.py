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

	URL_BLOCKED = 'URL_BLOCKED'  # permanent error (manually set)
	URL_LOAD_ERROR = 'URL_LOAD_ERROR'  # probably permanent error (set by playwright or manually)
	STEP_LIMIT_REACHED = 'STEP_LIMIT_REACHED'
	ACTION_PARSING_ERROR = 'ACTION_PARSING_ERROR'  # should be a rerun
	LLM_ERROR = 'LLM_ERROR'  # should be a rerun
	ABORTED_BY_LLM = 'ABORTED_BY_LLM'  # should define a better reason later (TODO: remove and add an auto trigger to get an AgentError)


class AgentErrors(Enum):
	"""Errors that the agent can encounter."""

	OPTION_SELECTION_ERROR = 'OPTION_SELECTION_ERROR'
	FILTER_ERROR = 'FILTER_ERROR'
	CLICK_ERROR = 'CLICK_ERROR'
	NAVIGATION_ERROR = 'NAVIGATION_ERROR'
	SCROLL_ERROR = 'SCROLL_ERROR'
	INPUT_ERROR = 'INPUT_ERROR'  # includes search errors
	HUMAN_VERIFICATION_ERROR = 'HUMAN_VERIFICATION_ERROR'
	PAGE_LOAD_ERROR = 'PAGE_LOAD_ERROR'
	PAGE_BLOCKED_ERROR = 'PAGE_BLOCKED_ERROR'
	OTHER = 'OTHER'

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


class SpecialRunErrors(Enum):
	"""Special errors that can occur during a run of the agent."""

	URL_LOAD_ERROR = 'URL_LOAD_ERROR'  # probably permanent error, set by playwright
	STEP_LIMIT_ERROR = 'STEP_LIMIT_ERROR'  # in the evaluation the script determines a more specific error
	LLM_ACTION_PARSING_ERROR = 'LLM_ACTION_PARSING_ERROR'  # should be a rerun
	LLM_ERROR = 'LLM_ERROR'  # should be a rerun
	LLM_ABORTED_ERROR = 'LLM_ABORTED_ERROR'  # in the evaluation the script determines a more specific error


class AgentErrors(Enum):
	"""
	Final errors that the agent can encounter.

	These are all the errors an agent can encounter after an evaluation.
	During the evaluation the STEP_LIMIT_ERRORs & LLM_ACTION_PARSING_ERRORs are evaluated and set to a more specific error.

	The AgentErrors include all the errors that can occur during a run of the agent.
	LLM_ERROR includes LLM_ACTION_PARSING_ERROR & LLM_ERROR from the SpecialRunErrors.
	"""

	# TODO: find a better way to combine those with the special errors (maybe make it one enum)
	# (maybe remove dublicate actions (URL_BLOCKED -> PAGE_BLOCKED_ERROR, URL_LOAD_ERROR -> PAGE_LOAD_ERROR))
	# (affects the agent analyzer)
	# (issue ex.: CLICK_action error set during runis not propagated to the agent analyzer)

	OPTION_SELECTION_ERROR = 'OPTION_SELECTION_ERROR'
	FILTER_ERROR = 'FILTER_ERROR'
	CLICK_ERROR = 'CLICK_ERROR'
	NAVIGATION_ERROR = 'NAVIGATION_ERROR'
	SCROLL_ERROR = 'SCROLL_ERROR'
	INPUT_ERROR = 'INPUT_ERROR'  # includes search errors
	HUMAN_VERIFICATION_ERROR = 'HUMAN_VERIFICATION_ERROR'
	PAGE_LOAD_ERROR = 'PAGE_LOAD_ERROR'  # probably permanent error (set by playwright, or by evaluator)
	PAGE_BLOCKED_ERROR = 'PAGE_BLOCKED_ERROR'  # usually permanent error (manually set, or by evaluator)
	LLM_ERROR = 'LLM_ERROR'  # should be a rerun - includes LLM_ACTION_PARSING_ERROR
	OTHER = 'OTHER'

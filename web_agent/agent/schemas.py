from pydantic import BaseModel, Field


class Task(BaseModel):
	"""The task to be completed."""

	identifier: str = Field(description='The id of the task.')
	description: str = Field(description='The task to be completed.')
	url: str = Field(description='The url to be loaded.')


class AgentDecision(BaseModel):
	"""The decision of the agent which action/function call to perform next."""

	thought: str = Field(description='Your reasoning process and next step.')
	action: str = Field(
		description="The function call to the action to perform next, chosen from the available actions. Example: click_by_text('text')"
	)

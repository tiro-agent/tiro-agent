from pydantic import BaseModel, Field


class Task(BaseModel):
	"""The task to be completed."""

	description: str = Field(description='The task to be completed.')
	url: str = Field(description='The url to be loaded.')
	output_dir: str = Field(description='The output directory.')

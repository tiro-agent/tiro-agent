import pandera.pandas as pa
from pandera.typing import Series
from pydantic import BaseModel

from web_agent.agent.schemas import AgentErrors


class Result(BaseModel):
	task_number: int
	identifier: str
	level: str
	success: bool
	ai_success_eval: bool | None = None
	error_type: str | None = None
	ai_error_type: AgentErrors | None = None
	human_error_type: AgentErrors | None = None


class ResultSchema(pa.DataFrameModel):
	task_number: Series[int]
	identifier: Series[str]
	level: Series[str]
	success: Series[bool]
	ai_success_eval: Series[bool] = pa.Field(nullable=True, coerce=True)
	error_type: Series[str] = pa.Field(nullable=True)
	ai_error_type: Series[str] = pa.Field(nullable=True)
	human_error_type: Series[str] = pa.Field(nullable=True)

	class Config:
		coerce = True
		strict = True


class TaskErrorEvaluation(BaseModel):
	thought_process: str
	cause: AgentErrors

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
	error_type: str | None = None  # final evaluation of the error (human > AI > run)
	run_error_type: str | None = None  # error type from the run
	ai_error_type: str | None = None  # error type from the AI evaluation
	human_error_type: str | None = None  # error type from the human evaluation


class ResultSchema(pa.DataFrameModel):
	task_number: Series[int]
	identifier: Series[str]
	level: Series[str]
	success: Series[bool]
	ai_success_eval: Series[bool] = pa.Field(nullable=True, coerce=True)
	error_type: Series[str] = pa.Field(nullable=True)
	run_error_type: Series[str] = pa.Field(nullable=True)
	ai_error_type: Series[str] = pa.Field(nullable=True)
	human_error_type: Series[str] = pa.Field(nullable=True)

	class Config:
		coerce = True
		strict = True


class TaskErrorEvaluation(BaseModel):
	thought_process: str
	cause: AgentErrors

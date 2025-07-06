import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series
from pydantic import BaseModel

from web_agent.agent.schemas import AgentErrors


class Result(BaseModel):
	"""
	Represents a single result of a task.
	"""

	task_number: int
	identifier: str
	level: str
	success: bool
	steps: int | None = None
	error_type: str | None = None  # final evaluation of the error (human > AI > run)
	run_error_type: str | None = None  # error type from the run, e.g. API error (set during run in error.txt)
	ai_error_type: str | None = None  # error type from the AI evaluation, e.g. navigation issue (set in ErrorEvaluator & saved to ai.eval)
	human_error_type: str | None = None  # error type from the human evaluation (set in human.eval)


class ResultSchema(pa.DataFrameModel):
	"""
	Schema of Result to support DataFrames.
	"""

	task_number: Series[int]
	identifier: Series[str]
	level: Series[str]
	success: Series[bool]
	steps: Series[pd.Int64Dtype] = pa.Field(nullable=True)
	error_type: Series[str] = pa.Field(nullable=True)
	run_error_type: Series[str] = pa.Field(nullable=True)
	ai_error_type: Series[str] = pa.Field(nullable=True)
	human_error_type: Series[str] = pa.Field(nullable=True)

	class Config:
		coerce = True
		strict = True


class TaskErrorEvaluation(BaseModel):
	"""
	Represents the evaluation of a task error.
	"""

	thought_process: str
	cause: AgentErrors

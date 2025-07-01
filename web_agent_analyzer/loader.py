import json
import os
from pathlib import Path

import pandas as pd
from pandera.typing import DataFrame

from web_agent.agent.schemas import SpecialAgentErrors
from web_agent_analyzer.schemas import Result, ResultSchema


def load_results(run_path: Path) -> DataFrame[ResultSchema]:
	results: list[Result] = []
	unfinished_tasks: list[str] = []

	for task in os.listdir(run_path):
		task_path: Path = run_path / task
		if not task_path.is_dir():
			continue

		error_file_path = task_path / 'error.txt'
		if error_file_path.exists():
			with open(error_file_path) as f:
				error_type = f.read().strip()
		else:
			error_type = None

		results_file_path: Path = task_path / 'result.json'
		if results_file_path.exists():
			with open(results_file_path) as f:
				result_json_data = json.load(f)
				task_result = Result(
					task_number=result_json_data['number'],
					identifier=result_json_data['task_id'],
					level=result_json_data['level'],
					success=True if error_type is None else False,
					run_error_type=error_type,
				)
				results.append(task_result)
		else:
			if task.startswith('#analysis'):
				continue
			unfinished_tasks.append(task)

	if len(unfinished_tasks) > 0:
		print(f'Found {len(unfinished_tasks)} unfinished tasks')
		for task in unfinished_tasks:
			task_number = task.split('_')[0]
			print(f'{task_number}')
		print('-' * 100)

	results_df = _results_to_df(results)

	return ResultSchema.validate(results_df)


def clean_results(results: DataFrame[ResultSchema]) -> DataFrame[ResultSchema]:
	ignored_error_types = [
		SpecialAgentErrors.LLM_ERROR.value,
		SpecialAgentErrors.URL_BLOCKED.value,
		SpecialAgentErrors.URL_LOAD_ERROR.value,
	]
	results_to_remove = results[results[ResultSchema.run_error_type].isin(ignored_error_types)]
	results_cleaned = results[~results.index.isin(results_to_remove.index)]
	return results_cleaned


def _results_to_df(results: list[Result]) -> pd.DataFrame:
	results_data = [result.model_dump() for result in results]
	results_df = pd.DataFrame(results_data)
	results_df = results_df.sort_values(by='task_number')
	return results_df

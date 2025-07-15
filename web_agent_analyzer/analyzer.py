import time
from pathlib import Path

from pandera.typing import DataFrame
from tqdm import tqdm

from web_agent.agent.schemas import AgentErrors, SpecialRunErrors
from web_agent_analyzer.error_evaluator import ErrorEvaluator
from web_agent_analyzer.loader import load_results
from web_agent_analyzer.reporter import generate_plots, generate_summary
from web_agent_analyzer.schemas import Result, ResultSchema


class ResultAnalyzer:
	"""
	Main class to analyze the results of a specific run ID, generating a summary of relevant statistics and plotting different error types.
	"""

	def __init__(self, run_id: str) -> None:
		"""
		Initializes the ResultAnalyzer with a specific run ID.
		"""
		self.run_id = run_id
		self.output_folder = Path('output').resolve()
		self.run_path = self.output_folder / run_id
		self.analysis_folder = self.run_path / '#analysis'

		if not self.run_path.exists():
			raise FileNotFoundError(f'Run directory {self.run_path} does not exist')

		if not self.analysis_folder.exists():
			self.analysis_folder.mkdir(parents=True, exist_ok=True)

		self.results: DataFrame[ResultSchema] = load_results(self.run_path)
		self.error_evaluator = ErrorEvaluator(self.analysis_folder)
		self.is_evaluated = False

	def save_results(self, filename: str = 'results.csv') -> None:
		"""
		Saves the evaluated results to a CSV file.
		"""
		if not self.is_evaluated:
			raise ValueError('Results are not evaluated, skipping saving')

		self.results.to_csv(self.analysis_folder / filename, sep=';', index=False)

	def generate_summary(self, print_summary: bool = True) -> None:
		"""
		Generates a summary of relevant statistics for the evaluated results.
		"""
		if not self.is_evaluated:
			raise ValueError('Results are not evaluated, skipping summary')

		generate_summary(self.results, self.analysis_folder, print_summary)

	def generate_plots(self) -> None:
		"""
		Generates error type plots.
		"""
		if not self.is_evaluated:
			raise ValueError('Results are not evaluated, skipping plots')

		generate_plots(self.results, self.analysis_folder)

	def evaluate_all_tasks(self) -> None:
		"""
		Evaluates all tasks in the run.
		"""
		if self.is_evaluated:
			raise ValueError('Results are already evaluated, skipping evaluation')

		errors_to_evaluate = [
			SpecialRunErrors.STEP_LIMIT_ERROR.value,
			SpecialRunErrors.LLM_ABORTED_ERROR.value,
		]

		for _, task_row in tqdm(self.results.iterrows(), desc='Evaluating all tasks', total=len(self.results)):
			task_result = Result(**task_row.to_dict())

			if task_result.run_error_type in errors_to_evaluate:
				ai_eval_executed = self._evaluate_single_task_error(task_result)
				if ai_eval_executed:
					time.sleep(4)
				continue
			else:
				final_error_type = self._get_final_error_type(task_result)
				self.results.loc[task_row.name, ResultSchema.error_type] = final_error_type

		self.is_evaluated = True
		print('Results evaluated')

	def _evaluate_single_task_error(self, task_result: Result) -> bool:
		"""
		Evaluates the error of a single task.
		"""
		task_path = self.run_path / f'{task_result.task_number:03d}_{task_result.identifier}'

		ai_eval_executed = False
		ai_eval = None

		human_eval_file_path = task_path / 'human.eval'
		ai_eval_file_path = task_path / 'ai.eval'
		human_eval = None
		if human_eval_file_path.exists():
			with open(human_eval_file_path) as f:
				human_eval = f.read().strip()

		elif ai_eval_file_path.exists():
			with open(ai_eval_file_path) as f:
				ai_eval_str = f.read().strip()
				ai_eval = ai_eval_str if ai_eval_str else None
		else:
			print(f'Evaluating task {task_result.task_number} with LLM')
			ai_eval_result = self.error_evaluator.evaluate_task_error(task_result, task_path)
			ai_eval = ai_eval_result.value if ai_eval_result else None
			ai_eval_executed = True
			if ai_eval:
				with open(ai_eval_file_path, 'w') as f:
					f.write(ai_eval)

		task_index = self.results[self.results[ResultSchema.task_number] == task_result.task_number].index
		if not task_index.empty:
			self.results.loc[task_index, ResultSchema.human_error_type] = human_eval
			self.results.loc[task_index, ResultSchema.ai_error_type] = ai_eval
			task_result.human_error_type = human_eval
			task_result.ai_error_type = ai_eval

		self.results.loc[task_index, ResultSchema.error_type] = self._get_final_error_type(task_result)
		return ai_eval_executed

	def _get_final_error_type(self, task_result: Result) -> str | None:  # noqa PLR0911
		"""
		Assign final error type based on prior evaluation.
		"""
		if task_result.human_error_type:
			return task_result.human_error_type
		if task_result.ai_error_type:
			return task_result.ai_error_type
		if task_result.run_error_type:
			if task_result.run_error_type == SpecialRunErrors.URL_LOAD_ERROR.value:
				return AgentErrors.PAGE_LOAD_ERROR.value
			elif task_result.run_error_type == SpecialRunErrors.LLM_ERROR.value:
				return AgentErrors.LLM_ERROR.value
			elif task_result.run_error_type == SpecialRunErrors.LLM_ACTION_PARSING_ERROR.value:
				return AgentErrors.LLM_ERROR.value
			elif task_result.run_error_type in AgentErrors.__members__:
				return task_result.run_error_type
			else:
				return AgentErrors.OTHER.value
		else:
			return None

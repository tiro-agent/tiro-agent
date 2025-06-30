import time
from pathlib import Path

from pandera.typing import DataFrame
from tqdm import tqdm

from web_agent.agent.schemas import SpecialAgentErrors
from web_agent_analyzer.error_evaluator import ErrorEvaluator
from web_agent_analyzer.loader import clean_results, load_results
from web_agent_analyzer.reporter import generate_plots, generate_summary
from web_agent_analyzer.schemas import Result, ResultSchema


class ResultAnalyzer:
	def __init__(self, run_id: str) -> None:
		self.run_id = run_id
		self.output_folder = Path('output').resolve()
		self.run_path = self.output_folder / run_id
		self.analysis_folder = self.run_path / '#analysis'

		if not self.run_path.exists():
			raise FileNotFoundError(f'Run directory {self.run_path} does not exist')

		if not self.analysis_folder.exists():
			self.analysis_folder.mkdir(parents=True, exist_ok=True)

		self.results: DataFrame[ResultSchema] = load_results(self.run_path)
		self.results_cleaned: DataFrame[ResultSchema] = clean_results(self.results)
		self.error_evaluator = ErrorEvaluator()

	def save_results(self, filename: str = 'results.csv') -> None:
		self.results.to_csv(self.analysis_folder / filename, sep=';', index=False)

	def generate_summary(self, print_summary: bool = True) -> None:
		generate_summary(self.results, self.results_cleaned, self.analysis_folder, print_summary)

	def generate_plots(self) -> None:
		generate_plots(self.results_cleaned, self.analysis_folder)

	def evaluate_tasks_with_errors(self) -> None:
		errors_to_evaluate = [
			SpecialAgentErrors.STEP_LIMIT_REACHED.value,
			SpecialAgentErrors.ABORTED_BY_LLM.value,
		]
		tasks_to_evaluate = self.results[self.results[ResultSchema.error_type].isin(errors_to_evaluate)]
		print(f'Found {len(tasks_to_evaluate)} tasks with errors to evaluate')

		if tasks_to_evaluate.empty:
			return

		for _, task_row in tqdm(tasks_to_evaluate.iterrows(), desc='Evaluating tasks', total=len(tasks_to_evaluate)):
			task_result = Result(**task_row.to_dict())
			self._evaluate_single_task_error(task_result)
			time.sleep(4)
		print('Results evaluated')

	def _evaluate_single_task_error(self, task_result: Result) -> None:
		task_path = self.run_path / f'{task_result.task_number:03d}_{task_result.identifier}'

		human_eval_file_path = task_path / 'human.eval'
		human_eval = None
		if human_eval_file_path.exists():
			with open(human_eval_file_path) as f:
				human_eval = f.read().strip()

		ai_eval_file_path = task_path / 'ai.eval'
		if ai_eval_file_path.exists():
			with open(ai_eval_file_path) as f:
				ai_eval_str = f.read().strip()
				ai_eval = ai_eval_str if ai_eval_str else None
		else:
			ai_eval_result = self.error_evaluator.evaluate_task_error(task_result, task_path)
			ai_eval = ai_eval_result.value if ai_eval_result else None
			if ai_eval:
				with open(ai_eval_file_path, 'w') as f:
					f.write(ai_eval)

		task_index = self.results[self.results[ResultSchema.task_number] == task_result.task_number].index
		if not task_index.empty:
			self.results.loc[task_index, ResultSchema.human_error_type] = human_eval
			self.results.loc[task_index, ResultSchema.ai_error_type] = ai_eval

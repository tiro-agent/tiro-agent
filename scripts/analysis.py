import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel


class Result(BaseModel):
	task_number: int
	level: str
	success: bool
	error_type: str | None = None


class ResultAnalyzer:
	def __init__(self, run_id: str) -> None:
		self.run_id = run_id
		script_dir = Path(__file__).parent.resolve()
		self.output_folder = script_dir / '../output'
		self.run_path = self.output_folder / run_id
		self.analysis_folder = self.run_path / '#analysis'

		if not self.run_path.exists():
			raise FileNotFoundError(f'Run directory {self.run_path} does not exist')

		if not self.analysis_folder.exists():
			self.analysis_folder.mkdir(parents=True, exist_ok=True)

		self.results = self._analysis()
		self.results_cleaned = self._clean_results()
		self.results_evaluated = None

	def save_results(self) -> None:
		self.results.to_csv(self.analysis_folder / 'results.csv', sep=';', index=False)

	def generate_summary(self, print_summary: bool = True) -> None:
		summary = ''
		summary += 'SUMMARY\n'
		summary += f'Found {len(self.results)} tasks\n'
		summary += '-' * 100 + '\n'
		summary += 'After cleaning (removing LLM_ERROR, URL_BLOCKED, URL_LOAD_ERROR)\n\n'
		summary += f'Found {len(self.results_cleaned)} tasks after cleaning\n'
		summary += f'Successfully completed tasks: {len(self.results_cleaned[self.results_cleaned["success"]])}\n'
		summary += f'Success rate: {len(self.results_cleaned[self.results_cleaned["success"]]) / len(self.results_cleaned) * 100:.2f}%\n'
		summary += '\nSuccess rate by level:\n'
		for level in self.results_cleaned['level'].unique():
			level_tasks = self.results_cleaned[self.results_cleaned['level'] == level]
			successful_level_tasks = self.results_cleaned[(self.results_cleaned['level'] == level) & (self.results_cleaned['success'])]
			success_rate = len(successful_level_tasks) / len(level_tasks) * 100
			summary += f'{level}: {success_rate:.2f}% ({len(successful_level_tasks)}/{len(level_tasks)})\n'
		summary += '\nSpecial error types:\n'
		for error_type in self.results_cleaned['error_type'].unique():
			if error_type is None:
				continue
			summary += f'{error_type}: {len(self.results_cleaned[self.results_cleaned["error_type"] == error_type])}\n'

		summary += '-' * 100 + '\n'

		llm_error_tasks = self.results[self.results['error_type'] == SpecialAgentErrors.LLM_ERROR.value]
		summary += f'Found {len(llm_error_tasks)} tasks with LLM_ERROR\n'
		for task_number in llm_error_tasks['task_number']:
			summary += f'{task_number} '
		summary += '\n' + '-' * 100 + '\n'

		url_blocked_tasks = self.results[self.results['error_type'] == SpecialAgentErrors.URL_BLOCKED.value]
		summary += f'Found {len(url_blocked_tasks)} tasks with URL_BLOCKED\n'
		for task_number in url_blocked_tasks['task_number']:
			summary += f'{task_number} '
		summary += '\n' + '-' * 100 + '\n'

		url_load_error_tasks = self.results[self.results['error_type'] == SpecialAgentErrors.URL_LOAD_ERROR.value]
		summary += f'Found {len(url_load_error_tasks)} tasks with URL_LOAD_ERROR\n'
		for task_number in url_load_error_tasks['task_number']:
			summary += f'{task_number} '
		summary += '\n' + '-' * 100 + '\n'

		if print_summary:
			print(summary)

		with open(self.analysis_folder / 'summary.txt', 'w') as f:
			f.write(summary)

	def generate_plots(self) -> None:
		self._generate_plot_success_rate()
		self._generate_plot_success_rate_by_level()
		self._generate_plot_error_types_pre_evaluation()

	def _clean_results(self) -> pd.DataFrame:
		# remove all the tasks that have a error type LLM_ERROR, URL_BLOCKED, URL_LOAD_ERROR
		ignored_error_types = [
			SpecialAgentErrors.LLM_ERROR.value,
			SpecialAgentErrors.URL_BLOCKED.value,
			SpecialAgentErrors.URL_LOAD_ERROR.value,
		]
		results_to_remove = self.results[self.results['error_type'].isin(ignored_error_types)]
		results_cleaned = self.results[~self.results.index.isin(results_to_remove.index)]
		return results_cleaned

	def _analysis(self) -> pd.DataFrame:
		results = []
		unfinished_tasks = []

		for task in os.listdir(self.run_path):
			task_path: Path = self.run_path / task
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
						level=result_json_data['level'],
						success=True if error_type is None else False,
						error_type=error_type,
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

		results_df = self._results_to_df(results)

		return results_df

	def _results_to_df(self, results: list[Result]) -> pd.DataFrame:
		results_data = [result.model_dump() for result in results]
		results_df = pd.DataFrame(results_data)
		results_df = results_df.sort_values(by='task_number')
		return results_df

	def _generate_plot_success_rate(self) -> None:
		success_counts = self.results['success'].value_counts()
		plt.figure(figsize=(10, 5))
		plt.pie(success_counts.values, labels=['Failed', 'Success'], autopct='%1.1f%%')
		plt.title('Success Rate')
		plt.savefig(self.analysis_folder / 'success_rate.png')
		plt.close()

	def _generate_plot_success_rate_by_level(self) -> None:
		# use matplotlib to generate a pie charts for each level of the success rate
		for level in self.results['level'].unique():
			level_df = self.results[self.results['level'] == level]

			# Count successes and failures
			success_counts = level_df['success'].value_counts()

			plt.figure(figsize=(10, 5))
			plt.pie(success_counts.values, labels=['Failed', 'Success'], autopct='%1.1f%%')
			plt.title(f'Success Rate for {level.capitalize()} Level Tasks')
			plt.savefig(self.analysis_folder / f'success_rate_by_level_{level}.png')
			plt.close()

	def _generate_plot_error_types_pre_evaluation(self) -> None:
		# use matplotlib to generate a pie chart for error types (excluding successful tasks)
		error_counts = self.results[self.results['error_type'].notna()]['error_type'].value_counts()

		if len(error_counts) > 0:
			plt.figure(figsize=(10, 5))
			plt.pie(error_counts.values, labels=error_counts.index, autopct='%1.1f%%')
			plt.title('Distribution of Error Types (Failed Tasks Only)')
			plt.savefig(self.analysis_folder / 'error_types_pre_evaluation.png')
			plt.close()
		else:
			print('No errors found - all tasks were successful!')


if __name__ == '__main__':
	run_id = 'try_threading_4'
	results_analyzer = ResultAnalyzer(run_id)
	results_analyzer.generate_summary()
	results_analyzer.save_results()
	results_analyzer.generate_plots()

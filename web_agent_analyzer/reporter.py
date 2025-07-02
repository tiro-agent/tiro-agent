from pathlib import Path

import matplotlib.pyplot as plt
from pandera.typing import DataFrame

from web_agent_analyzer.loader import clean_results
from web_agent_analyzer.schemas import ResultSchema


def generate_summary(results: DataFrame[ResultSchema], analysis_folder: Path, print_summary: bool = True) -> None:
	errors_removed, results_cleaned = clean_results(results)

	summary = ''
	summary += 'SUMMARY\n'
	summary += f'Found {len(results)} tasks\n'
	summary += '-' * 100 + '\n'
	summary += 'Errors removed:\n\n'
	for error_type in errors_removed:
		summary += f'{error_type}: {len(results[results[ResultSchema.error_type] == error_type])}\n'
	summary += '\n\nLLM_ERROR includes action parsing error.\n'
	summary += '-' * 100 + '\n'
	summary += 'After cleaning: \n\n'
	summary += f'Found {len(results_cleaned)} tasks after cleaning\n'
	summary += f'Successfully completed tasks: {len(results_cleaned[results_cleaned[ResultSchema.success]])}\n'
	summary += f'Success rate: {len(results_cleaned[results_cleaned[ResultSchema.success]]) / len(results_cleaned) * 100:.2f}%\n'
	summary += '\nSuccess rate by level:\n'
	for level in results_cleaned[ResultSchema.level].unique():
		level_tasks = results_cleaned[results_cleaned[ResultSchema.level] == level]
		successful_level_tasks = results_cleaned[(results_cleaned[ResultSchema.level] == level) & (results_cleaned[ResultSchema.success])]
		success_rate = len(successful_level_tasks) / len(level_tasks) * 100
		summary += f'{level}: {success_rate:.2f}% ({len(successful_level_tasks)}/{len(level_tasks)})\n'
	summary += '\nError types:\n'
	for error_type in results_cleaned[ResultSchema.error_type].unique():
		if error_type is None:
			continue
		summary += f'{error_type}: {len(results_cleaned[results_cleaned[ResultSchema.error_type] == error_type])}\n'
	summary += '-' * 100 + '\n'

	summary += 'Tasks for each error type:\n\n'

	for error_type in results[ResultSchema.error_type].unique():
		if error_type is None:
			continue
		summary += f'Found {len(results[results[ResultSchema.error_type] == error_type])} tasks with {error_type}\n'
		for task_number in results[results[ResultSchema.error_type] == error_type][ResultSchema.task_number]:
			summary += f'{task_number} '
		summary += '\n\n'

	if print_summary:
		print(summary)

	with open(analysis_folder / 'summary.txt', 'w') as f:
		f.write(summary)


def generate_plots(results: DataFrame[ResultSchema], analysis_folder: Path) -> None:
	_, results_cleaned = clean_results(results)
	_generate_plot_success_rate(results_cleaned, analysis_folder)
	_generate_plot_success_rate_by_level(results_cleaned, analysis_folder)
	_generate_plot_run_error_types(results, analysis_folder)
	_generate_plot_error_types(results, analysis_folder)
	_generate_plot_error_types(results_cleaned, analysis_folder, filename='error_types_cleaned.png')
	_generate_plot_error_types_by_level(results, analysis_folder)
	_generate_plot_error_types_by_level(results_cleaned, analysis_folder, filename_prefix='error_types_cleaned_by_level')


def _generate_plot_success_rate(
	results_cleaned: DataFrame[ResultSchema], analysis_folder: Path, filename: str = 'success_rate.png'
) -> None:
	successful_tasks_count = results_cleaned[results_cleaned[ResultSchema.success]].shape[0]
	failed_tasks_count = results_cleaned[~results_cleaned[ResultSchema.success]].shape[0]

	if successful_tasks_count == 0 and failed_tasks_count == 0:
		return

	sizes = [failed_tasks_count, successful_tasks_count]
	labels = ['Failed', 'Success']

	plt.figure(figsize=(10, 5))
	plt.pie(sizes, labels=labels, autopct='%1.1f%%')
	plt.title('Success Rate')
	plt.savefig(analysis_folder / filename)
	plt.close()


def _generate_plot_success_rate_by_level(
	results_cleaned: DataFrame[ResultSchema], analysis_folder: Path, filename_prefix: str = 'success_rate_by_level'
) -> None:
	unique_levels = results_cleaned[ResultSchema.level].unique()
	if len(unique_levels) == 0 or unique_levels[0] is None:
		return
	for level in unique_levels:
		level_df = results_cleaned[results_cleaned[ResultSchema.level] == level]
		if len(level_df) == 0:
			continue
		successful_level_tasks_count = level_df[level_df[ResultSchema.success]].shape[0]
		failed_level_tasks_count = level_df[~level_df[ResultSchema.success]].shape[0]

		if successful_level_tasks_count == 0 and failed_level_tasks_count == 0:
			continue

		sizes = [failed_level_tasks_count, successful_level_tasks_count]
		labels = ['Failed', 'Success']

		plt.figure(figsize=(10, 5))
		plt.pie(sizes, labels=labels, autopct='%1.1f%%')
		plt.title(f'Success Rate for {level.capitalize()} Level Tasks')
		plt.savefig(analysis_folder / f'{filename_prefix}_{level}.png')
		plt.close()


def _generate_plot_run_error_types(results: DataFrame[ResultSchema], analysis_folder: Path, filename: str = 'run_error_types.png') -> None:
	failed_tasks = results[results[ResultSchema.run_error_type].notna()]
	if len(failed_tasks) == 0:
		print('No errors found - all tasks were successful!')
		return
	error_counts = failed_tasks[ResultSchema.run_error_type].value_counts()
	if len(error_counts) > 0:
		plt.figure(figsize=(10, 5))
		plt.pie(error_counts.values, labels=error_counts.index, autopct='%1.1f%%')
		plt.title('Distribution of Run Error Types (Failed Tasks Only)')
		plt.savefig(analysis_folder / filename)
		plt.close()


def _generate_plot_error_types(results: DataFrame[ResultSchema], analysis_folder: Path, filename: str = 'error_types.png') -> None:
	# results are already post-evaluation
	failed_tasks = results[results[ResultSchema.error_type].notna()]
	if len(failed_tasks) == 0:
		print('No errors found - all tasks were successful!')
		return
	error_counts = failed_tasks[ResultSchema.error_type].value_counts()
	if len(error_counts) > 0:
		plt.figure(figsize=(10, 5))
		plt.pie(error_counts.values, labels=error_counts.index, autopct='%1.1f%%')
		plt.title('Distribution of Final Error Types (Failed Tasks Only)')
		plt.savefig(analysis_folder / filename)
		plt.close()


def _generate_plot_error_types_by_level(
	results: DataFrame[ResultSchema], analysis_folder: Path, filename_prefix: str = 'error_types_by_level'
) -> None:
	unique_levels = results[ResultSchema.level].unique()
	if len(unique_levels) == 0 or unique_levels[0] is None:
		return
	for level in unique_levels:
		level_df = results[results[ResultSchema.level] == level]
		if len(level_df) == 0:
			continue

		failed_tasks = level_df[level_df[ResultSchema.error_type].notna()]
		if len(failed_tasks) == 0:
			print(f'No errors found for level {level} - all tasks were successful!')
			continue
		error_counts = failed_tasks[ResultSchema.error_type].value_counts()
		if len(error_counts) > 0:
			plt.figure(figsize=(10, 5))
			plt.pie(error_counts.values, labels=error_counts.index, autopct='%1.1f%%')
			plt.title(f'Distribution of Error Types for {level.capitalize()} Level Tasks (Post-Evaluation)')
			plt.savefig(analysis_folder / f'{filename_prefix}_{level}.png')
			plt.close()
